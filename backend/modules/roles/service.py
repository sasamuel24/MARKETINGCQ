"""
Servicio de roles - Lógica de negocio
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from modules.roles.repository import RoleRepository
from modules.roles.schemas import RoleCreate, RoleUpdate, RoleResponse


class RoleService:
    """Servicio para gestionar la lógica de negocio de roles"""
    
    def __init__(self, db: Session):
        self.repository = RoleRepository(db)
    
    def get_role_by_id(self, role_id: int) -> RoleResponse:
        """
        Obtener rol por ID
        
        Args:
            role_id: ID del rol
            
        Returns:
            Rol encontrado
            
        Raises:
            HTTPException: Si el rol no existe
        """
        role = self.repository.get_by_id(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rol con ID {role_id} no encontrado"
            )
        return RoleResponse.model_validate(role)
    
    def get_all_roles(self, skip: int = 0, limit: int = 100) -> tuple[List[RoleResponse], int]:
        """
        Obtener todos los roles con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            
        Returns:
            Tupla con (lista de roles, total de roles)
        """
        roles = self.repository.get_all(skip=skip, limit=limit)
        total = self.repository.count()
        return [RoleResponse.model_validate(role) for role in roles], total
    
    def create_role(self, role_data: RoleCreate) -> RoleResponse:
        """
        Crear un nuevo rol
        
        Args:
            role_data: Datos del rol a crear
            
        Returns:
            Rol creado
            
        Raises:
            HTTPException: Si el nombre ya existe
        """
        # Verificar si el nombre ya existe
        if self.repository.exists_by_nombre(role_data.nombre):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un rol con el nombre '{role_data.nombre}'"
            )
        
        try:
            role = self.repository.create(role_data)
            return RoleResponse.model_validate(role)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un rol con el nombre '{role_data.nombre}'"
            )
    
    def update_role(self, role_id: int, role_data: RoleUpdate) -> RoleResponse:
        """
        Actualizar un rol existente
        
        Args:
            role_id: ID del rol a actualizar
            role_data: Datos a actualizar
            
        Returns:
            Rol actualizado
            
        Raises:
            HTTPException: Si el rol no existe o el nuevo nombre ya está en uso
        """
        # Verificar que el rol existe
        if not self.repository.exists(role_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rol con ID {role_id} no encontrado"
            )
        
        # Verificar si el nuevo nombre ya existe (excluyendo el rol actual)
        if role_data.nombre and self.repository.exists_by_nombre(role_data.nombre, exclude_id=role_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un rol con el nombre '{role_data.nombre}'"
            )
        
        try:
            role = self.repository.update(role_id, role_data)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Rol con ID {role_id} no encontrado"
                )
            return RoleResponse.model_validate(role)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un rol con el nombre '{role_data.nombre}'"
            )
    
    def delete_role(self, role_id: int) -> None:
        """
        Eliminar un rol
        
        Args:
            role_id: ID del rol a eliminar
            
        Raises:
            HTTPException: Si el rol no existe o tiene usuarios asociados
        """
        # Verificar que el rol existe
        if not self.repository.exists(role_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rol con ID {role_id} no encontrado"
            )
        
        # Verificar que no tenga usuarios asociados
        if self.repository.has_users(role_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede eliminar el rol porque tiene usuarios asociados. Primero reasigne los usuarios a otro rol."
            )
        
        if not self.repository.delete(role_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rol con ID {role_id} no encontrado"
            )
    
    def get_role_by_nombre(self, nombre: str) -> Optional[RoleResponse]:
        """
        Obtener rol por nombre
        
        Args:
            nombre: Nombre del rol
            
        Returns:
            Rol encontrado o None
        """
        role = self.repository.get_by_nombre(nombre)
        if role:
            return RoleResponse.model_validate(role)
        return None
