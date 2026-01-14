"""
Router de roles - Endpoints REST para gestión de roles
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from modules.roles.schemas import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleListResponse
)
from modules.roles.service import RoleService
from core.dependencies import get_current_user_id
from db.session import get_db


router = APIRouter(prefix="/roles", tags=["Roles"])


def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    """Dependency para obtener instancia de RoleService"""
    return RoleService(db)


@router.get("", response_model=RoleListResponse, status_code=status.HTTP_200_OK)
async def get_roles(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    service: RoleService = Depends(get_role_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener lista de roles con paginación
    
    - **page**: Número de página (por defecto 1)
    - **page_size**: Tamaño de página (por defecto 10, máximo 100)
    
    Requiere autenticación.
    """
    skip = (page - 1) * page_size
    roles, total = service.get_all_roles(skip=skip, limit=page_size)
    
    return RoleListResponse(
        roles=roles,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{role_id}", response_model=RoleResponse, status_code=status.HTTP_200_OK)
async def get_role(
    role_id: int,
    service: RoleService = Depends(get_role_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener un rol por ID
    
    - **role_id**: ID del rol a obtener
    
    Requiere autenticación.
    """
    return service.get_role_by_id(role_id)


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    service: RoleService = Depends(get_role_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Crear un nuevo rol
    
    - **nombre**: Nombre del rol (único, obligatorio)
    
    Requiere autenticación.
    """
    return service.create_role(role_data)


@router.put("/{role_id}", response_model=RoleResponse, status_code=status.HTTP_200_OK)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    service: RoleService = Depends(get_role_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Actualizar un rol existente
    
    - **role_id**: ID del rol a actualizar
    - **nombre**: Nuevo nombre del rol (opcional)
    
    Requiere autenticación.
    """
    return service.update_role(role_id, role_data)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    service: RoleService = Depends(get_role_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Eliminar un rol
    
    - **role_id**: ID del rol a eliminar
    
    Requiere autenticación.
    """
    service.delete_role(role_id)
    return None
