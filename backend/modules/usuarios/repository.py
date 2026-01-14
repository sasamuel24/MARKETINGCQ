"""
Repositorio para operaciones con usuarios en la base de datos
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from db.models import User
from modules.usuarios.schemas import UserCreate, UserUpdate


class UserRepository:
    """Repositorio para gestionar operaciones CRUD de usuarios"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int, include_relations: bool = False) -> Optional[User]:
        """
        Obtener usuario por ID
        
        Args:
            user_id: ID del usuario
            include_relations: Si True, incluye rol y área
            
        Returns:
            Usuario encontrado o None
        """
        query = self.db.query(User)
        if include_relations:
            query = query.options(joinedload(User.rol), joinedload(User.area))
        return query.filter(User.id == user_id).first()
    
    def get_by_email(self, email: str, include_relations: bool = False) -> Optional[User]:
        """
        Obtener usuario por email
        
        Args:
            email: Email del usuario
            include_relations: Si True, incluye rol y área
            
        Returns:
            Usuario encontrado o None
        """
        query = self.db.query(User)
        if include_relations:
            query = query.options(joinedload(User.rol), joinedload(User.area))
        return query.filter(User.email == email).first()
    
    def get_all(self, skip: int = 0, limit: int = 100, include_relations: bool = True) -> List[User]:
        """
        Obtener todos los usuarios con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            include_relations: Si True, incluye rol y área
            
        Returns:
            Lista de usuarios
        """
        query = self.db.query(User)
        if include_relations:
            query = query.options(joinedload(User.rol), joinedload(User.area))
        return query.offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """
        Contar total de usuarios
        
        Returns:
            Número total de usuarios
        """
        return self.db.query(User).count()
    
    def create(self, user_data: dict) -> User:
        """
        Crear un nuevo usuario
        
        Args:
            user_data: Diccionario con datos del usuario (debe incluir password_hash)
            
        Returns:
            Usuario creado
            
        Raises:
            IntegrityError: Si el email ya existe
        """
        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user_id: int, user_data: dict) -> Optional[User]:
        """
        Actualizar un usuario existente
        
        Args:
            user_id: ID del usuario a actualizar
            user_data: Diccionario con datos a actualizar
            
        Returns:
            Usuario actualizado o None si no existe
            
        Raises:
            IntegrityError: Si el nuevo email ya existe
        """
        user = self.get_by_id(user_id)
        if not user:
            return None
        
        # Actualizar solo campos proporcionados
        for key, value in user_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """
        Eliminar un usuario
        
        Args:
            user_id: ID del usuario a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
    
    def exists(self, user_id: int) -> bool:
        """
        Verificar si existe un usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            True si existe, False si no
        """
        return self.db.query(User).filter(User.id == user_id).count() > 0
    
    def exists_by_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """
        Verificar si existe un usuario con el email dado
        
        Args:
            email: Email del usuario
            exclude_id: ID a excluir de la búsqueda (útil para actualizaciones)
            
        Returns:
            True si existe, False si no
        """
        query = self.db.query(User).filter(User.email == email)
        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)
        return query.count() > 0
    
    def get_by_rol_id(self, rol_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Obtener usuarios por rol
        
        Args:
            rol_id: ID del rol
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            
        Returns:
            Lista de usuarios
        """
        return self.db.query(User).filter(User.rol_id == rol_id).offset(skip).limit(limit).all()
    
    def get_by_area_id(self, area_id: int, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Obtener usuarios por área
        
        Args:
            area_id: ID del área
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            
        Returns:
            Lista de usuarios
        """
        return self.db.query(User).filter(User.area_id == area_id).offset(skip).limit(limit).all()
