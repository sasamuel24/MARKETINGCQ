"""
Router de usuarios - Endpoints REST para gestión de usuarios
"""
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from modules.usuarios.schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserDetailResponse,
    UserListResponse
)
from modules.usuarios.service import UserService
from core.dependencies import get_current_user_id
from db.session import get_db


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency para obtener instancia de UserService"""
    return UserService(db)


@router.get("", response_model=UserListResponse, status_code=status.HTTP_200_OK)
async def get_users(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    service: UserService = Depends(get_user_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener lista de usuarios con paginación
    
    - **page**: Número de página (por defecto 1)
    - **page_size**: Tamaño de página (por defecto 10, máximo 100)
    
    Incluye información de rol y área.
    Requiere autenticación.
    """
    skip = (page - 1) * page_size
    usuarios, total = service.get_all_users(skip=skip, limit=page_size)
    
    return UserListResponse(
        usuarios=usuarios,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{user_id}", response_model=UserDetailResponse, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener un usuario por ID
    
    - **user_id**: ID del usuario a obtener
    
    Incluye información de rol y área.
    Requiere autenticación.
    """
    return service.get_user_by_id(user_id)


@router.post("", response_model=UserDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Crear un nuevo usuario
    
    - **full_name**: Nombre completo del usuario (obligatorio)
    - **email**: Email único del usuario (obligatorio)
    - **password**: Contraseña (mínimo 8 caracteres, obligatorio)
    - **rol_id**: ID del rol asignado (obligatorio)
    - **area_id**: ID del área asignada (obligatorio)
    
    La contraseña se hashea automáticamente antes de guardar.
    Requiere autenticación.
    """
    return service.create_user(user_data)


@router.put("/{user_id}", response_model=UserDetailResponse, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Actualizar un usuario existente
    
    - **user_id**: ID del usuario a actualizar
    - **full_name**: Nuevo nombre completo (opcional)
    - **email**: Nuevo email (opcional)
    - **password**: Nueva contraseña (opcional)
    - **rol_id**: Nuevo rol (opcional)
    - **area_id**: Nueva área (opcional)
    
    Todos los campos son opcionales. Solo se actualizan los campos proporcionados.
    Si se proporciona contraseña, se hashea automáticamente.
    Requiere autenticación.
    """
    return service.update_user(user_id, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Eliminar un usuario
    
    - **user_id**: ID del usuario a eliminar
    
    Requiere autenticación.
    """
    service.delete_user(user_id)
    return None
