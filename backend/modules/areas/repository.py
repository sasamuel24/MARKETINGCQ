"""
Repositorio para operaciones con áreas en la base de datos
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.models import Area
from modules.areas.schemas import AreaCreate, AreaUpdate


class AreaRepository:
    """Repositorio para gestionar operaciones CRUD de áreas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, area_id: int) -> Optional[Area]:
        """
        Obtener área por ID
        
        Args:
            area_id: ID del área
            
        Returns:
            Área encontrada o None
        """
        return self.db.query(Area).filter(Area.id == area_id).first()
    
    def get_by_nombre(self, nombre: str) -> Optional[Area]:
        """
        Obtener área por nombre
        
        Args:
            nombre: Nombre del área
            
        Returns:
            Área encontrada o None
        """
        return self.db.query(Area).filter(Area.nombre == nombre).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Area]:
        """
        Obtener todas las áreas con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            
        Returns:
            Lista de áreas
        """
        return self.db.query(Area).offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """
        Contar total de áreas
        
        Returns:
            Número total de áreas
        """
        return self.db.query(Area).count()
    
    def create(self, area_data: AreaCreate) -> Area:
        """
        Crear una nueva área
        
        Args:
            area_data: Datos del área a crear
            
        Returns:
            Área creada
            
        Raises:
            IntegrityError: Si el nombre ya existe
        """
        area = Area(nombre=area_data.nombre)
        self.db.add(area)
        self.db.commit()
        self.db.refresh(area)
        return area
    
    def update(self, area_id: int, area_data: AreaUpdate) -> Optional[Area]:
        """
        Actualizar un área existente
        
        Args:
            area_id: ID del área a actualizar
            area_data: Datos a actualizar
            
        Returns:
            Área actualizada o None si no existe
            
        Raises:
            IntegrityError: Si el nuevo nombre ya existe
        """
        area = self.get_by_id(area_id)
        if not area:
            return None
        
        # Actualizar solo campos proporcionados
        if area_data.nombre is not None:
            area.nombre = area_data.nombre
        
        self.db.commit()
        self.db.refresh(area)
        return area
    
    def delete(self, area_id: int) -> bool:
        """
        Eliminar un área
        
        Args:
            area_id: ID del área a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        area = self.get_by_id(area_id)
        if not area:
            return False
        
        self.db.delete(area)
        self.db.commit()
        return True
    
    def exists(self, area_id: int) -> bool:
        """
        Verificar si existe un área por ID
        
        Args:
            area_id: ID del área
            
        Returns:
            True si existe, False si no
        """
        return self.db.query(Area).filter(Area.id == area_id).count() > 0
    
    def exists_by_nombre(self, nombre: str, exclude_id: Optional[int] = None) -> bool:
        """
        Verificar si existe un área con el nombre dado
        
        Args:
            nombre: Nombre del área
            exclude_id: ID a excluir de la búsqueda (útil para actualizaciones)
            
        Returns:
            True si existe, False si no
        """
        query = self.db.query(Area).filter(Area.nombre == nombre)
        if exclude_id is not None:
            query = query.filter(Area.id != exclude_id)
        return query.count() > 0
