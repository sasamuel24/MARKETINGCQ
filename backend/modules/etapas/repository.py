"""
Repositorio para operaciones con etapas en la base de datos
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from db.models import Etapa
from modules.etapas.schemas import EtapaCreate, EtapaUpdate


class EtapaRepository:
    """Repositorio para gestionar operaciones CRUD de etapas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, etapa_id: int, include_relations: bool = False) -> Optional[Etapa]:
        """
        Obtener etapa por ID
        
        Args:
            etapa_id: ID de la etapa
            include_relations: Si True, incluye área
            
        Returns:
            Etapa encontrada o None
        """
        query = self.db.query(Etapa)
        if include_relations:
            query = query.options(joinedload(Etapa.area))
        return query.filter(Etapa.id == etapa_id).first()
    
    def get_by_area_and_code(self, area_id: int, code: str) -> Optional[Etapa]:
        """
        Obtener etapa por área y código
        
        Args:
            area_id: ID del área
            code: Código de la etapa
            
        Returns:
            Etapa encontrada o None
        """
        return self.db.query(Etapa).filter(
            Etapa.area_id == area_id,
            Etapa.code == code
        ).first()
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        area_id: Optional[int] = None,
        only_active: bool = False,
        include_relations: bool = True
    ) -> List[Etapa]:
        """
        Obtener todas las etapas con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            area_id: Filtrar por área (opcional)
            only_active: Si True, solo retorna etapas activas
            include_relations: Si True, incluye área
            
        Returns:
            Lista de etapas ordenadas por área y order
        """
        query = self.db.query(Etapa)
        if include_relations:
            query = query.options(joinedload(Etapa.area))
        if area_id:
            query = query.filter(Etapa.area_id == area_id)
        if only_active:
            query = query.filter(Etapa.is_active == True)
        return query.order_by(Etapa.area_id, Etapa.order).offset(skip).limit(limit).all()
    
    def count(self, area_id: Optional[int] = None, only_active: bool = False) -> int:
        """
        Contar total de etapas
        
        Args:
            area_id: Filtrar por área (opcional)
            only_active: Si True, solo cuenta etapas activas
            
        Returns:
            Número total de etapas
        """
        query = self.db.query(Etapa)
        if area_id:
            query = query.filter(Etapa.area_id == area_id)
        if only_active:
            query = query.filter(Etapa.is_active == True)
        return query.count()
    
    def create(self, etapa_data: EtapaCreate) -> Etapa:
        """
        Crear una nueva etapa
        
        Args:
            etapa_data: Datos de la etapa a crear
            
        Returns:
            Etapa creada
            
        Raises:
            IntegrityError: Si ya existe una etapa con el mismo code u order en el área
        """
        etapa = Etapa(
            area_id=etapa_data.area_id,
            code=etapa_data.code,
            label=etapa_data.label,
            order=etapa_data.order,
            is_active=etapa_data.is_active,
            approval_mode=etapa_data.approval_mode
        )
        self.db.add(etapa)
        self.db.commit()
        self.db.refresh(etapa)
        return etapa
    
    def update(self, etapa_id: int, etapa_data: EtapaUpdate) -> Optional[Etapa]:
        """
        Actualizar una etapa existente
        
        Args:
            etapa_id: ID de la etapa a actualizar
            etapa_data: Datos a actualizar
            
        Returns:
            Etapa actualizada o None si no existe
            
        Raises:
            IntegrityError: Si el nuevo code u order ya existe en el área
        """
        etapa = self.get_by_id(etapa_id)
        if not etapa:
            return None
        
        # Actualizar solo campos proporcionados
        if etapa_data.code is not None:
            etapa.code = etapa_data.code
        if etapa_data.label is not None:
            etapa.label = etapa_data.label
        if etapa_data.order is not None:
            etapa.order = etapa_data.order
        if etapa_data.is_active is not None:
            etapa.is_active = etapa_data.is_active
        if etapa_data.approval_mode is not None:
            etapa.approval_mode = etapa_data.approval_mode
        
        self.db.commit()
        self.db.refresh(etapa)
        return etapa
    
    def delete(self, etapa_id: int) -> bool:
        """
        Eliminar una etapa
        
        Args:
            etapa_id: ID de la etapa a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        etapa = self.get_by_id(etapa_id)
        if not etapa:
            return False
        
        self.db.delete(etapa)
        self.db.commit()
        return True
    
    def exists(self, etapa_id: int) -> bool:
        """
        Verificar si existe una etapa por ID
        
        Args:
            etapa_id: ID de la etapa
            
        Returns:
            True si existe, False si no
        """
        return self.db.query(Etapa).filter(Etapa.id == etapa_id).count() > 0
    
    def exists_by_area_and_code(
        self, 
        area_id: int, 
        code: str, 
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Verificar si existe una etapa con el código dado en el área
        
        Args:
            area_id: ID del área
            code: Código de la etapa
            exclude_id: ID a excluir de la búsqueda (útil para actualizaciones)
            
        Returns:
            True si existe, False si no
        """
        query = self.db.query(Etapa).filter(
            Etapa.area_id == area_id,
            Etapa.code == code
        )
        if exclude_id is not None:
            query = query.filter(Etapa.id != exclude_id)
        return query.count() > 0
    
    def exists_by_area_and_order(
        self, 
        area_id: int, 
        order: int, 
        exclude_id: Optional[int] = None
    ) -> bool:
        """
        Verificar si existe una etapa con el orden dado en el área
        
        Args:
            area_id: ID del área
            order: Orden de la etapa
            exclude_id: ID a excluir de la búsqueda (útil para actualizaciones)
            
        Returns:
            True si existe, False si no
        """
        query = self.db.query(Etapa).filter(
            Etapa.area_id == area_id,
            Etapa.order == order
        )
        if exclude_id is not None:
            query = query.filter(Etapa.id != exclude_id)
        return query.count() > 0
    
    def get_by_area(self, area_id: int, only_active: bool = True) -> List[Etapa]:
        """
        Obtener todas las etapas de un área ordenadas por order
        
        Args:
            area_id: ID del área
            only_active: Si True, solo retorna etapas activas
            
        Returns:
            Lista de etapas
        """
        query = self.db.query(Etapa).filter(Etapa.area_id == area_id)
        if only_active:
            query = query.filter(Etapa.is_active == True)
        return query.order_by(Etapa.order).all()
