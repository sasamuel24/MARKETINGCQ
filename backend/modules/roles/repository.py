"""
Repositorio para operaciones con roles en la base de datos
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.models import Role
from modules.roles.schemas import RoleCreate, RoleUpdate


class RoleRepository:
    """Repositorio para gestionar operaciones CRUD de roles"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, role_id: int) -> Optional[Role]:
        """
        Obtener rol por ID
        
        Args:
            role_id: ID del rol
            
        Returns:
            Rol encontrado o None
        """
        return self.db.query(Role).filter(Role.id == role_id).first()
    
    def get_by_nombre(self, nombre: str) -> Optional[Role]:
        """
        Obtener rol por nombre
        
        Args:
            nombre: Nombre del rol
            
        Returns:
            Rol encontrado o None
        """
        return self.db.query(Role).filter(Role.nombre == nombre).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Role]:
        """
        Obtener todos los roles con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            
        Returns:
            Lista de roles
        """
        return self.db.query(Role).offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """
        Contar total de roles
        
        Returns:
            Número total de roles
        """
        return self.db.query(Role).count()
    
    def create(self, role_data: RoleCreate) -> Role:
        """
        Crear un nuevo rol
        
        Args:
            role_data: Datos del rol a crear
            
        Returns:
            Rol creado
            
        Raises:
            IntegrityError: Si el nombre ya existe
        """
        role = Role(nombre=role_data.nombre)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def update(self, role_id: int, role_data: RoleUpdate) -> Optional[Role]:
        """
        Actualizar un rol existente
        
        Args:
            role_id: ID del rol a actualizar
            role_data: Datos a actualizar
            
        Returns:
            Rol actualizado o None si no existe
            
        Raises:
            IntegrityError: Si el nuevo nombre ya existe
        """
        role = self.get_by_id(role_id)
        if not role:
            return None
        
        # Actualizar solo campos proporcionados
        if role_data.nombre is not None:
            role.nombre = role_data.nombre
        
        self.db.commit()
        self.db.refresh(role)
        return role
    
    def delete(self, role_id: int) -> bool:
        """
        Eliminar un rol
        
        Args:
            role_id: ID del rol a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        role = self.get_by_id(role_id)
        if not role:
            return False
        
        self.db.delete(role)
        self.db.commit()
        return True
    
    def exists(self, role_id: int) -> bool:
        """
        Verificar si existe un rol por ID
        
        Args:
            role_id: ID del rol
            
        Returns:
            True si existe, False si no
        """
        return self.db.query(Role).filter(Role.id == role_id).count() > 0
    
    def exists_by_nombre(self, nombre: str, exclude_id: Optional[int] = None) -> bool:
        """
        Verificar si existe un rol con el nombre dado
        
        Args:
            nombre: Nombre del rol
            exclude_id: ID a excluir de la búsqueda (útil para actualizaciones)
            
        Returns:
            True si existe, False si no
        """
        query = self.db.query(Role).filter(Role.nombre == nombre)
        if exclude_id is not None:
            query = query.filter(Role.id != exclude_id)
        return query.count() > 0
