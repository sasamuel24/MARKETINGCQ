"""
Router de áreas - Endpoints REST para gestión de áreas
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from modules.areas.schemas import (
    AreaCreate,
    AreaUpdate,
    AreaResponse,
    AreaListResponse
)
from modules.areas.service import AreaService
from core.dependencies import get_current_user_id
from db.session import get_db


router = APIRouter(prefix="/areas", tags=["Áreas"])


def get_area_service(db: Session = Depends(get_db)) -> AreaService:
    """Dependency para obtener instancia de AreaService"""
    return AreaService(db)


@router.get("", response_model=AreaListResponse, status_code=status.HTTP_200_OK)
async def get_areas(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    service: AreaService = Depends(get_area_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener lista de áreas con paginación
    
    - **page**: Número de página (por defecto 1)
    - **page_size**: Tamaño de página (por defecto 10, máximo 100)
    
    Requiere autenticación.
    """
    skip = (page - 1) * page_size
    areas, total = service.get_all_areas(skip=skip, limit=page_size)
    
    return AreaListResponse(
        areas=areas,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{area_id}", response_model=AreaResponse, status_code=status.HTTP_200_OK)
async def get_area(
    area_id: int,
    service: AreaService = Depends(get_area_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener un área por ID
    
    - **area_id**: ID del área a obtener
    
    Requiere autenticación.
    """
    return service.get_area_by_id(area_id)


@router.post("", response_model=AreaResponse, status_code=status.HTTP_201_CREATED)
async def create_area(
    area_data: AreaCreate,
    service: AreaService = Depends(get_area_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Crear una nueva área
    
    - **nombre**: Nombre del área (único, obligatorio)
    
    Requiere autenticación.
    """
    return service.create_area(area_data)


@router.put("/{area_id}", response_model=AreaResponse, status_code=status.HTTP_200_OK)
async def update_area(
    area_id: int,
    area_data: AreaUpdate,
    service: AreaService = Depends(get_area_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Actualizar un área existente
    
    - **area_id**: ID del área a actualizar
    - **nombre**: Nuevo nombre del área (opcional)
    
    Requiere autenticación.
    """
    return service.update_area(area_id, area_data)


@router.delete("/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_area(
    area_id: int,
    service: AreaService = Depends(get_area_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Eliminar un área
    
    - **area_id**: ID del área a eliminar
    
    Requiere autenticación.
    """
    service.delete_area(area_id)
    return None
