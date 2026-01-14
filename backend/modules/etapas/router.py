"""
Router de etapas - Endpoints REST para gestión de etapas del flujo por área
"""
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from modules.etapas.schemas import (
    EtapaCreate,
    EtapaUpdate,
    EtapaResponse,
    EtapaDetailResponse,
    EtapaListResponse
)
from modules.etapas.service import EtapaService
from core.dependencies import get_current_user_id
from db.session import get_db


router = APIRouter(prefix="/etapas", tags=["Etapas"])


def get_etapa_service(db: Session = Depends(get_db)) -> EtapaService:
    """Dependency para obtener instancia de EtapaService"""
    return EtapaService(db)


@router.get("", response_model=EtapaListResponse, status_code=status.HTTP_200_OK)
async def get_etapas(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    area_id: Optional[int] = Query(None, description="Filtrar por área"),
    only_active: bool = Query(False, description="Filtrar solo etapas activas"),
    service: EtapaService = Depends(get_etapa_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener lista de etapas con paginación
    
    - **page**: Número de página (por defecto 1)
    - **page_size**: Tamaño de página (por defecto 10, máximo 100)
    - **area_id**: Filtrar por área específica (opcional)
    - **only_active**: Si True, solo retorna etapas activas
    
    Las etapas se retornan ordenadas por área y order.
    Incluye información del área relacionada.
    Requiere autenticación.
    """
    skip = (page - 1) * page_size
    etapas, total = service.get_all_etapas(
        skip=skip, 
        limit=page_size,
        area_id=area_id,
        only_active=only_active
    )
    
    return EtapaListResponse(
        etapas=etapas,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/area/{area_id}", response_model=List[EtapaResponse], status_code=status.HTTP_200_OK)
async def get_etapas_by_area(
    area_id: int,
    only_active: bool = Query(True, description="Filtrar solo etapas activas"),
    service: EtapaService = Depends(get_etapa_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener todas las etapas de un área ordenadas por 'order'
    
    - **area_id**: ID del área
    - **only_active**: Si True, solo retorna etapas activas (default: True)
    
    Útil para obtener el flujo completo de un área.
    Requiere autenticación.
    """
    return service.get_etapas_by_area(area_id, only_active=only_active)


@router.get("/{etapa_id}", response_model=EtapaDetailResponse, status_code=status.HTTP_200_OK)
async def get_etapa(
    etapa_id: int,
    service: EtapaService = Depends(get_etapa_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener una etapa por ID
    
    - **etapa_id**: ID de la etapa a obtener
    
    Incluye información del área relacionada.
    Requiere autenticación.
    """
    return service.get_etapa_by_id(etapa_id)


@router.post("", response_model=EtapaDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_etapa(
    etapa_data: EtapaCreate,
    service: EtapaService = Depends(get_etapa_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Crear una nueva etapa
    
    - **area_id**: ID del área (obligatorio)
    - **code**: Código de la etapa (obligatorio, único por área)
    - **label**: Etiqueta visible (obligatorio)
    - **order**: Orden en el flujo (obligatorio, único por área, >= 0)
    - **is_active**: Si la etapa está activa (opcional, default: True)
    - **approval_mode**: Modo de aprobación: "ANY" o "ALL" (opcional, default: "ANY")
    
    El código y el orden deben ser únicos dentro del área.
    Requiere autenticación.
    """
    return service.create_etapa(etapa_data)


@router.put("/{etapa_id}", response_model=EtapaDetailResponse, status_code=status.HTTP_200_OK)
async def update_etapa(
    etapa_id: int,
    etapa_data: EtapaUpdate,
    service: EtapaService = Depends(get_etapa_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Actualizar una etapa existente
    
    - **etapa_id**: ID de la etapa a actualizar
    - **code**: Nuevo código (opcional, debe ser único por área)
    - **label**: Nueva etiqueta (opcional)
    - **order**: Nuevo orden (opcional, debe ser único por área)
    - **is_active**: Cambiar si está activa (opcional)
    - **approval_mode**: Cambiar modo de aprobación (opcional)
    
    Todos los campos son opcionales. Solo se actualizan los campos proporcionados.
    El código y orden deben ser únicos dentro del área.
    No se puede cambiar el área de una etapa (eliminar y recrear).
    Requiere autenticación.
    """
    return service.update_etapa(etapa_id, etapa_data)


@router.delete("/{etapa_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_etapa(
    etapa_id: int,
    service: EtapaService = Depends(get_etapa_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Eliminar una etapa
    
    - **etapa_id**: ID de la etapa a eliminar
    
    Requiere autenticación.
    """
    service.delete_etapa(etapa_id)
    return None
