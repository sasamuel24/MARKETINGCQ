"""
Router de solicitudes - Endpoints REST para gestión de solicitudes
"""
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from modules.solicitudes.schemas import (
    SolicitudCreate,
    SolicitudUpdate,
    SolicitudResponse,
    SolicitudDetailResponse,
    SolicitudListResponse
)
from modules.solicitudes.service import SolicitudService
from core.dependencies import get_current_user_id
from db.session import get_db


router = APIRouter(prefix="/solicitudes", tags=["Solicitudes"])


def get_solicitud_service(db: Session = Depends(get_db)) -> SolicitudService:
    """Dependency para obtener instancia de SolicitudService"""
    return SolicitudService(db)


@router.get("", response_model=SolicitudListResponse, status_code=status.HTTP_200_OK)
async def get_solicitudes(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    area_id: Optional[int] = Query(None, description="Filtrar por área"),
    stage_id: Optional[int] = Query(None, description="Filtrar por etapa"),
    status_id: Optional[int] = Query(None, description="Filtrar por estado"),
    created_by_user_id: Optional[int] = Query(None, description="Filtrar por usuario creador"),
    check_approver: bool = Query(False, description="Si es True, filtra solicitudes donde el usuario actual es aprobador"),
    service: SolicitudService = Depends(get_solicitud_service),
    current_user_id: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener lista de solicitudes con paginación y filtros
    
    - **page**: Número de página (por defecto 1)
    - **page_size**: Tamaño de página (por defecto 10, máximo 100)
    - **area_id**: Filtrar por área específica (opcional)
    - **stage_id**: Filtrar por etapa específica (opcional)
    - **status_id**: Filtrar por estado específico (opcional)
    - **created_by_user_id**: Filtrar por usuario creador (opcional)
    - **check_approver**: Si es True, retorna solo solicitudes donde el usuario actual es aprobador de la etapa actual
    
    Las solicitudes se retornan ordenadas por fecha de creación descendente.
    Incluye información completa de área, etapa (stage), estado (state) y usuario creador.
    Requiere autenticación.
    """
    skip = (page - 1) * page_size
    
    approver_user_id = int(current_user_id) if check_approver else None
    
    solicitudes, total = service.get_all_solicitudes(
        skip=skip, 
        limit=page_size,
        area_id=area_id,
        stage_id=stage_id,
        status_id=status_id,
        created_by_user_id=created_by_user_id,
        approver_user_id=approver_user_id
    )
    
    return SolicitudListResponse(
        solicitudes=solicitudes,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/area/{area_id}", response_model=List[SolicitudDetailResponse], status_code=status.HTTP_200_OK)
async def get_solicitudes_by_area(
    area_id: int,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener todas las solicitudes de un área
    
    - **area_id**: ID del área
    
    Retorna todas las solicitudes del área ordenadas por fecha de creación descendente.
    Requiere autenticación.
    """
    return service.get_solicitudes_by_area(area_id)


@router.get("/user/{user_id}", response_model=List[SolicitudDetailResponse], status_code=status.HTTP_200_OK)
async def get_solicitudes_by_user(
    user_id: int,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener todas las solicitudes creadas por un usuario
    
    - **user_id**: ID del usuario
    
    Retorna todas las solicitudes creadas por el usuario ordenadas por fecha de creación descendente.
    Requiere autenticación.
    """
    return service.get_solicitudes_by_user(user_id)


@router.get("/{solicitud_id}", response_model=SolicitudDetailResponse, status_code=status.HTTP_200_OK)
async def get_solicitud(
    solicitud_id: int,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener una solicitud por ID
    
    - **solicitud_id**: ID de la solicitud a obtener
    
    Incluye información completa de área, etapa (stage), estado (state) y usuario creador.
    Requiere autenticación.
    """
    return service.get_solicitud_by_id(solicitud_id)


@router.post("", response_model=SolicitudDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_solicitud(
    solicitud: SolicitudCreate,
    service: SolicitudService = Depends(get_solicitud_service),
    current_user_id: str = Depends(get_current_user_id)  # Usuario autenticado
):
    """
    Crear una nueva solicitud
    
    - **title**: Título de la solicitud (requerido)
    - **description**: Descripción detallada (opcional)
    - **area_id**: ID del área (debe existir)
    - **stage_id**: ID de la etapa (debe existir y pertenecer al área)
    - **status_id**: ID del estado (debe existir)
    
    VALIDACIÓN IMPORTANTE: La etapa (stage) debe pertenecer al área especificada.
    El usuario creador se obtiene del token JWT.
    Requiere autenticación.
    """
    return service.create_solicitud(solicitud, int(current_user_id))


@router.put("/{solicitud_id}", response_model=SolicitudDetailResponse, status_code=status.HTTP_200_OK)
async def update_solicitud(
    solicitud_id: int,
    solicitud: SolicitudUpdate,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Actualizar una solicitud existente
    
    - **solicitud_id**: ID de la solicitud a actualizar
    - **title**: Nuevo título (opcional)
    - **description**: Nueva descripción (opcional)
    - **stage_id**: Nueva etapa (opcional, debe pertenecer al área de la solicitud)
    - **status_id**: Nuevo estado (opcional)
    
    Solo se actualizan los campos proporcionados.
    VALIDACIÓN IMPORTANTE: Si se cambia la etapa, debe pertenecer al área de la solicitud.
    Requiere autenticación.
    """
    return service.update_solicitud(solicitud_id, solicitud)


@router.delete("/{solicitud_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_solicitud(
    solicitud_id: int,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Eliminar una solicitud
    
    - **solicitud_id**: ID de la solicitud a eliminar
    
    Requiere autenticación.
    """
    service.delete_solicitud(solicitud_id)
    return None
