"""
Router de etapa_aprobadores - Endpoints REST para gestión de aprobadores por etapa
"""
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from modules.etapa_aprobadores.schemas import (
    EtapaAprobadorCreate,
    EtapaAprobadorUpdate,
    EtapaAprobadorResponse,
    EtapaAprobadorDetailResponse,
    EtapaAprobadorListResponse
)
from modules.etapa_aprobadores.service import EtapaAprobadorService
from core.dependencies import get_current_user_id
from db.session import get_db


router = APIRouter(prefix="/etapa-aprobadores", tags=["Etapa Aprobadores"])


def get_etapa_aprobador_service(db: Session = Depends(get_db)) -> EtapaAprobadorService:
    """Dependency para obtener instancia de EtapaAprobadorService"""
    return EtapaAprobadorService(db)


@router.get("", response_model=EtapaAprobadorListResponse, status_code=status.HTTP_200_OK)
async def get_etapa_aprobadores(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros"),
    etapa_id: Optional[int] = Query(None, description="Filtrar por etapa"),
    user_id: Optional[int] = Query(None, description="Filtrar por usuario"),
    only_active: bool = Query(False, description="Filtrar solo asignaciones activas"),
    service: EtapaAprobadorService = Depends(get_etapa_aprobador_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener lista de asignaciones etapa-aprobador con paginación
    
    - **skip**: Número de registros a saltar (por defecto 0)
    - **limit**: Límite de registros (por defecto 100, máximo 100)
    - **etapa_id**: Filtrar por etapa específica (opcional)
    - **user_id**: Filtrar por usuario específico (opcional)
    - **only_active**: Si True, solo retorna asignaciones activas
    
    Las asignaciones se retornan ordenadas por etapa_id y user_id.
    Incluye información de la etapa y usuario relacionados.
    Requiere autenticación.
    """
    etapa_aprobadores, total = service.get_all_etapa_aprobadores(
        skip=skip, 
        limit=limit,
        etapa_id=etapa_id,
        user_id=user_id,
        only_active=only_active
    )
    
    return EtapaAprobadorListResponse(
        items=etapa_aprobadores,
        total=total
    )


@router.get("/etapa/{etapa_id}", response_model=List[EtapaAprobadorDetailResponse], status_code=status.HTTP_200_OK)
async def get_aprobadores_by_etapa(
    etapa_id: int,
    only_active: bool = Query(True, description="Filtrar solo aprobadores activos"),
    service: EtapaAprobadorService = Depends(get_etapa_aprobador_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener todos los aprobadores de una etapa específica
    
    - **etapa_id**: ID de la etapa
    - **only_active**: Si True, solo retorna aprobadores activos (default: True)
    
    Útil para saber qué usuarios pueden aprobar en una etapa.
    Requiere autenticación.
    """
    return service.get_aprobadores_by_etapa(etapa_id, only_active=only_active)


@router.get("/usuario/{user_id}", response_model=List[EtapaAprobadorDetailResponse], status_code=status.HTTP_200_OK)
async def get_etapas_by_usuario(
    user_id: int,
    only_active: bool = Query(True, description="Filtrar solo asignaciones activas"),
    service: EtapaAprobadorService = Depends(get_etapa_aprobador_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener todas las etapas donde el usuario es aprobador
    
    - **user_id**: ID del usuario
    - **only_active**: Si True, solo retorna asignaciones activas (default: True)
    
    Útil para saber en qué etapas puede aprobar un usuario.
    Requiere autenticación.
    """
    return service.get_etapas_by_usuario(user_id, only_active=only_active)


@router.get("/{etapa_aprobador_id}", response_model=EtapaAprobadorDetailResponse, status_code=status.HTTP_200_OK)
async def get_etapa_aprobador(
    etapa_aprobador_id: int,
    service: EtapaAprobadorService = Depends(get_etapa_aprobador_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener una asignación etapa-aprobador por ID
    
    - **etapa_aprobador_id**: ID de la asignación a obtener
    
    Incluye información de la etapa y usuario relacionados.
    Requiere autenticación.
    """
    return service.get_etapa_aprobador_by_id(etapa_aprobador_id)


@router.post("", response_model=EtapaAprobadorDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_etapa_aprobador(
    etapa_aprobador: EtapaAprobadorCreate,
    service: EtapaAprobadorService = Depends(get_etapa_aprobador_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Crear una nueva asignación etapa-aprobador
    
    - **etapa_id**: ID de la etapa (debe existir)
    - **user_id**: ID del usuario aprobador (debe existir)
    - **is_active**: Indica si la asignación está activa (default: True)
    
    La combinación etapa_id + user_id debe ser única.
    Requiere autenticación.
    """
    return service.create_etapa_aprobador(etapa_aprobador)


@router.put("/{etapa_aprobador_id}", response_model=EtapaAprobadorDetailResponse, status_code=status.HTTP_200_OK)
async def update_etapa_aprobador(
    etapa_aprobador_id: int,
    etapa_aprobador: EtapaAprobadorUpdate,
    service: EtapaAprobadorService = Depends(get_etapa_aprobador_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Actualizar una asignación etapa-aprobador existente
    
    - **etapa_aprobador_id**: ID de la asignación a actualizar
    - **is_active**: Nuevo estado de la asignación
    
    Solo se pueden actualizar los campos proporcionados.
    Requiere autenticación.
    """
    return service.update_etapa_aprobador(etapa_aprobador_id, etapa_aprobador)


@router.delete("/{etapa_aprobador_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_etapa_aprobador(
    etapa_aprobador_id: int,
    service: EtapaAprobadorService = Depends(get_etapa_aprobador_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Eliminar una asignación etapa-aprobador
    
    - **etapa_aprobador_id**: ID de la asignación a eliminar
    
    Requiere autenticación.
    """
    service.delete_etapa_aprobador(etapa_aprobador_id)
    return None
