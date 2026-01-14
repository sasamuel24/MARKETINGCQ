"""
Servicio de usuarios - Lógica de negocio
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from modules.usuarios.repository import UserRepository
from modules.usuarios.schemas import UserCreate, UserUpdate, UserResponse, UserDetailResponse
from modules.roles.repository import RoleRepository
from modules.areas.repository import AreaRepository
from core.security import get_password_hash


class UserService:
    """Servicio para gestionar la lógica de negocio de usuarios"""
    
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
        self.role_repository = RoleRepository(db)
        self.area_repository = AreaRepository(db)
    
    def get_user_by_id(self, user_id: int) -> UserDetailResponse:
        """
        Obtener usuario por ID con información de rol y área
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario encontrado
            
        Raises:
            HTTPException: Si el usuario no existe
        """
        user = self.repository.get_by_id(user_id, include_relations=True)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado"
            )
        return UserDetailResponse.model_validate(user)
    
    def get_all_users(self, skip: int = 0, limit: int = 100) -> tuple[List[UserDetailResponse], int]:
        """
        Obtener todos los usuarios con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            
        Returns:
            Tupla con (lista de usuarios, total de usuarios)
        """
        users = self.repository.get_all(skip=skip, limit=limit, include_relations=True)
        total = self.repository.count()
        return [UserDetailResponse.model_validate(user) for user in users], total
    
    def create_user(self, user_data: UserCreate) -> UserDetailResponse:
        """
        Crear un nuevo usuario
        
        Args:
            user_data: Datos del usuario a crear
            
        Returns:
            Usuario creado
            
        Raises:
            HTTPException: Si el email ya existe o rol/área no existen
        """
        # Verificar si el email ya existe
        if self.repository.exists_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un usuario con el email '{user_data.email}'"
            )
        
        # Verificar que el rol existe
        if not self.role_repository.exists(user_data.rol_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El rol con ID {user_data.rol_id} no existe"
            )
        
        # Verificar que el área existe
        if not self.area_repository.exists(user_data.area_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El área con ID {user_data.area_id} no existe"
            )
        
        # Hashear la contraseña
        password_hash = get_password_hash(user_data.password)
        
        # Preparar datos para crear usuario
        user_dict = {
            "full_name": user_data.full_name,
            "email": user_data.email,
            "password_hash": password_hash,
            "rol_id": user_data.rol_id,
            "area_id": user_data.area_id
        }
        
        try:
            user = self.repository.create(user_dict)
            # Recargar con relaciones
            user = self.repository.get_by_id(user.id, include_relations=True)
            return UserDetailResponse.model_validate(user)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un usuario con el email '{user_data.email}'"
            )
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> UserDetailResponse:
        """
        Actualizar un usuario existente
        
        Args:
            user_id: ID del usuario a actualizar
            user_data: Datos a actualizar
            
        Returns:
            Usuario actualizado
            
        Raises:
            HTTPException: Si el usuario no existe o el nuevo email ya está en uso
        """
        # Verificar que el usuario existe
        if not self.repository.exists(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado"
            )
        
        # Verificar si el nuevo email ya existe (excluyendo el usuario actual)
        if user_data.email and self.repository.exists_by_email(user_data.email, exclude_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un usuario con el email '{user_data.email}'"
            )
        
        # Verificar que el rol existe (si se proporciona)
        if user_data.rol_id and not self.role_repository.exists(user_data.rol_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El rol con ID {user_data.rol_id} no existe"
            )
        
        # Verificar que el área existe (si se proporciona)
        if user_data.area_id and not self.area_repository.exists(user_data.area_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El área con ID {user_data.area_id} no existe"
            )
        
        # Preparar datos para actualizar
        update_dict = {}
        if user_data.full_name is not None:
            update_dict["full_name"] = user_data.full_name
        if user_data.email is not None:
            update_dict["email"] = user_data.email
        if user_data.rol_id is not None:
            update_dict["rol_id"] = user_data.rol_id
        if user_data.area_id is not None:
            update_dict["area_id"] = user_data.area_id
        if user_data.password is not None:
            update_dict["password_hash"] = get_password_hash(user_data.password)
        
        try:
            user = self.repository.update(user_id, update_dict)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuario con ID {user_id} no encontrado"
                )
            # Recargar con relaciones
            user = self.repository.get_by_id(user.id, include_relations=True)
            return UserDetailResponse.model_validate(user)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un usuario con el email '{user_data.email}'"
            )
    
    def delete_user(self, user_id: int) -> None:
        """
        Eliminar un usuario
        
        Args:
            user_id: ID del usuario a eliminar
            
        Raises:
            HTTPException: Si el usuario no existe
        """
        if not self.repository.delete(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {user_id} no encontrado"
            )
    
    def get_user_by_email(self, email: str) -> Optional[UserDetailResponse]:
        """
        Obtener usuario por email
        
        Args:
            email: Email del usuario
            
        Returns:
            Usuario encontrado o None
        """
        user = self.repository.get_by_email(email, include_relations=True)
        if user:
            return UserDetailResponse.model_validate(user)
        return None
