"""
Router de estados - Endpoints REST para gestión de estados del flujo
"""
from typing import Annotated, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from modules.estados.schemas import (
    EstadoCreate,
    EstadoUpdate,
    EstadoResponse,
    EstadoListResponse
)
from modules.estados.service import EstadoService
from core.dependencies import get_current_user_id
from db.session import get_db


router = APIRouter(prefix="/estados", tags=["Estados"])


def get_estado_service(db: Session = Depends(get_db)) -> EstadoService:
    """Dependency para obtener instancia de EstadoService"""
    return EstadoService(db)


@router.get("", response_model=EstadoListResponse, status_code=status.HTTP_200_OK)
async def get_estados(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    only_active: bool = Query(False, description="Filtrar solo estados activos"),
    service: EstadoService = Depends(get_estado_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener lista de estados con paginación
    
    - **page**: Número de página (por defecto 1)
    - **page_size**: Tamaño de página (por defecto 10, máximo 100)
    - **only_active**: Si True, solo retorna estados activos
    
    Los estados se retornan ordenados por el campo 'order'.
    Requiere autenticación.
    """
    skip = (page - 1) * page_size
    estados, total = service.get_all_estados(skip=skip, limit=page_size, only_active=only_active)
    
    return EstadoListResponse(
        estados=estados,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/finales", response_model=List[EstadoResponse], status_code=status.HTTP_200_OK)
async def get_estados_finales(
    service: EstadoService = Depends(get_estado_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener todos los estados finales activos
    
    Útil para identificar estados que marcan el fin de un flujo.
    Requiere autenticación.
    """
    return service.get_final_estados()


@router.get("/{estado_id}", response_model=EstadoResponse, status_code=status.HTTP_200_OK)
async def get_estado(
    estado_id: int,
    service: EstadoService = Depends(get_estado_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener un estado por ID
    
    - **estado_id**: ID del estado a obtener
    
    Requiere autenticación.
    """
    return service.get_estado_by_id(estado_id)


@router.post("", response_model=EstadoResponse, status_code=status.HTTP_201_CREATED)
async def create_estado(
    estado_data: EstadoCreate,
    service: EstadoService = Depends(get_estado_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Crear un nuevo estado
    
    - **code**: Código único del estado (obligatorio, ej: "CREATED", "IN_REVIEW")
    - **label**: Etiqueta visible (obligatorio, ej: "Creado", "En Revisión")
    - **order**: Orden en el flujo (obligatorio, número >= 0)
    - **is_final**: Si es un estado final (opcional, default: False)
    - **is_active**: Si el estado está activo (opcional, default: True)
    
    Requiere autenticación.
    """
    return service.create_estado(estado_data)


@router.put("/{estado_id}", response_model=EstadoResponse, status_code=status.HTTP_200_OK)
async def update_estado(
    estado_id: int,
    estado_data: EstadoUpdate,
    service: EstadoService = Depends(get_estado_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Actualizar un estado existente
    
    - **estado_id**: ID del estado a actualizar
    - **code**: Nuevo código (opcional)
    - **label**: Nueva etiqueta (opcional)
    - **order**: Nuevo orden (opcional)
    - **is_final**: Cambiar si es final (opcional)
    - **is_active**: Cambiar si está activo (opcional)
    
    Todos los campos son opcionales. Solo se actualizan los campos proporcionados.
    Requiere autenticación.
    """
    return service.update_estado(estado_id, estado_data)


@router.delete("/{estado_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_estado(
    estado_id: int,
    service: EstadoService = Depends(get_estado_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Eliminar un estado
    
    - **estado_id**: ID del estado a eliminar
    
    Requiere autenticación.
    """
    service.delete_estado(estado_id)
    return None
