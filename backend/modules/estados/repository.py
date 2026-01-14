"""
Repositorio para operaciones con estados en la base de datos
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.models import Estado
from modules.estados.schemas import EstadoCreate, EstadoUpdate


class EstadoRepository:
    """Repositorio para gestionar operaciones CRUD de estados"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, estado_id: int) -> Optional[Estado]:
        """
        Obtener estado por ID
        
        Args:
            estado_id: ID del estado
            
        Returns:
            Estado encontrado o None
        """
        return self.db.query(Estado).filter(Estado.id == estado_id).first()
    
    def get_by_code(self, code: str) -> Optional[Estado]:
        """
        Obtener estado por código
        
        Args:
            code: Código del estado
            
        Returns:
            Estado encontrado o None
        """
        return self.db.query(Estado).filter(Estado.code == code).first()
    
    def get_all(self, skip: int = 0, limit: int = 100, only_active: bool = False) -> List[Estado]:
        """
        Obtener todos los estados con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            only_active: Si True, solo retorna estados activos
            
        Returns:
            Lista de estados ordenados por 'order'
        """
        query = self.db.query(Estado)
        if only_active:
            query = query.filter(Estado.is_active == True)
        return query.order_by(Estado.order).offset(skip).limit(limit).all()
    
    def count(self, only_active: bool = False) -> int:
        """
        Contar total de estados
        
        Args:
            only_active: Si True, solo cuenta estados activos
            
        Returns:
            Número total de estados
        """
        query = self.db.query(Estado)
        if only_active:
            query = query.filter(Estado.is_active == True)
        return query.count()
    
    def create(self, estado_data: EstadoCreate) -> Estado:
        """
        Crear un nuevo estado
        
        Args:
            estado_data: Datos del estado a crear
            
        Returns:
            Estado creado
            
        Raises:
            IntegrityError: Si el código ya existe
        """
        estado = Estado(
            code=estado_data.code,
            label=estado_data.label,
            order=estado_data.order,
            is_final=estado_data.is_final,
            is_active=estado_data.is_active
        )
        self.db.add(estado)
        self.db.commit()
        self.db.refresh(estado)
        return estado
    
    def update(self, estado_id: int, estado_data: EstadoUpdate) -> Optional[Estado]:
        """
        Actualizar un estado existente
        
        Args:
            estado_id: ID del estado a actualizar
            estado_data: Datos a actualizar
            
        Returns:
            Estado actualizado o None si no existe
            
        Raises:
            IntegrityError: Si el nuevo código ya existe
        """
        estado = self.get_by_id(estado_id)
        if not estado:
            return None
        
        # Actualizar solo campos proporcionados
        if estado_data.code is not None:
            estado.code = estado_data.code
        if estado_data.label is not None:
            estado.label = estado_data.label
        if estado_data.order is not None:
            estado.order = estado_data.order
        if estado_data.is_final is not None:
            estado.is_final = estado_data.is_final
        if estado_data.is_active is not None:
            estado.is_active = estado_data.is_active
        
        self.db.commit()
        self.db.refresh(estado)
        return estado
    
    def delete(self, estado_id: int) -> bool:
        """
        Eliminar un estado
        
        Args:
            estado_id: ID del estado a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        estado = self.get_by_id(estado_id)
        if not estado:
            return False
        
        self.db.delete(estado)
        self.db.commit()
        return True
    
    def exists(self, estado_id: int) -> bool:
        """
        Verificar si existe un estado por ID
        
        Args:
            estado_id: ID del estado
            
        Returns:
            True si existe, False si no
        """
        return self.db.query(Estado).filter(Estado.id == estado_id).count() > 0
    
    def exists_by_code(self, code: str, exclude_id: Optional[int] = None) -> bool:
        """
        Verificar si existe un estado con el código dado
        
        Args:
            code: Código del estado
            exclude_id: ID a excluir de la búsqueda (útil para actualizaciones)
            
        Returns:
            True si existe, False si no
        """
        query = self.db.query(Estado).filter(Estado.code == code)
        if exclude_id is not None:
            query = query.filter(Estado.id != exclude_id)
        return query.count() > 0
    
    def get_final_states(self) -> List[Estado]:
        """
        Obtener todos los estados finales activos
        
        Returns:
            Lista de estados finales
        """
        return self.db.query(Estado).filter(
            Estado.is_final == True,
            Estado.is_active == True
        ).order_by(Estado.order).all()
