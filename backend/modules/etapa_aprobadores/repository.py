"""
Repositorio para operaciones con etapa_aprobadores en la base de datos
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from db.models import EtapaAprobador
from modules.etapa_aprobadores.schemas import EtapaAprobadorCreate, EtapaAprobadorUpdate


class EtapaAprobadorRepository:
    """Repositorio para gestionar operaciones CRUD de etapa_aprobadores"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, etapa_aprobador_id: int, include_relations: bool = False) -> Optional[EtapaAprobador]:
        """
        Obtener etapa aprobador por ID
        
        Args:
            etapa_aprobador_id: ID del etapa aprobador
            include_relations: Si True, incluye etapa y usuario
            
        Returns:
            EtapaAprobador encontrado o None
        """
        query = self.db.query(EtapaAprobador)
        if include_relations:
            query = query.options(
                joinedload(EtapaAprobador.etapa),
                joinedload(EtapaAprobador.user)
            )
        return query.filter(EtapaAprobador.id == etapa_aprobador_id).first()
    
    def get_by_etapa_and_user(self, etapa_id: int, user_id: int) -> Optional[EtapaAprobador]:
        """
        Obtener asignación por etapa y usuario
        
        Args:
            etapa_id: ID de la etapa
            user_id: ID del usuario
            
        Returns:
            EtapaAprobador encontrado o None
        """
        return self.db.query(EtapaAprobador).filter(
            EtapaAprobador.etapa_id == etapa_id,
            EtapaAprobador.user_id == user_id
        ).first()
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        etapa_id: Optional[int] = None,
        user_id: Optional[int] = None,
        only_active: bool = False,
        include_relations: bool = True
    ) -> List[EtapaAprobador]:
        """
        Obtener todos los etapa aprobadores con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            etapa_id: Filtrar por etapa (opcional)
            user_id: Filtrar por usuario (opcional)
            only_active: Si True, solo retorna asignaciones activas
            include_relations: Si True, incluye etapa y usuario
            
        Returns:
            Lista de etapa aprobadores ordenados por etapa_id
        """
        query = self.db.query(EtapaAprobador)
        if include_relations:
            query = query.options(
                joinedload(EtapaAprobador.etapa),
                joinedload(EtapaAprobador.user)
            )
        if etapa_id:
            query = query.filter(EtapaAprobador.etapa_id == etapa_id)
        if user_id:
            query = query.filter(EtapaAprobador.user_id == user_id)
        if only_active:
            query = query.filter(EtapaAprobador.is_active == True)
        return query.order_by(EtapaAprobador.etapa_id, EtapaAprobador.user_id).offset(skip).limit(limit).all()
    
    def count(
        self, 
        etapa_id: Optional[int] = None, 
        user_id: Optional[int] = None,
        only_active: bool = False
    ) -> int:
        """
        Contar etapa aprobadores
        
        Args:
            etapa_id: Filtrar por etapa (opcional)
            user_id: Filtrar por usuario (opcional)
            only_active: Si True, solo cuenta asignaciones activas
            
        Returns:
            Número de etapa aprobadores
        """
        query = self.db.query(EtapaAprobador)
        if etapa_id:
            query = query.filter(EtapaAprobador.etapa_id == etapa_id)
        if user_id:
            query = query.filter(EtapaAprobador.user_id == user_id)
        if only_active:
            query = query.filter(EtapaAprobador.is_active == True)
        return query.count()
    
    def create(self, etapa_aprobador_data: EtapaAprobadorCreate) -> EtapaAprobador:
        """
        Crear un nuevo etapa aprobador
        
        Args:
            etapa_aprobador_data: Datos del etapa aprobador
            
        Returns:
            EtapaAprobador creado
            
        Raises:
            IntegrityError: Si hay un error de integridad (duplicado, FK inválida, etc.)
        """
        db_etapa_aprobador = EtapaAprobador(
            etapa_id=etapa_aprobador_data.etapa_id,
            user_id=etapa_aprobador_data.user_id,
            is_active=etapa_aprobador_data.is_active
        )
        self.db.add(db_etapa_aprobador)
        self.db.commit()
        self.db.refresh(db_etapa_aprobador)
        
        # Recargar con relaciones
        return self.get_by_id(db_etapa_aprobador.id, include_relations=True)
    
    def update(self, etapa_aprobador_id: int, etapa_aprobador_data: EtapaAprobadorUpdate) -> Optional[EtapaAprobador]:
        """
        Actualizar un etapa aprobador existente
        
        Args:
            etapa_aprobador_id: ID del etapa aprobador a actualizar
            etapa_aprobador_data: Datos a actualizar
            
        Returns:
            EtapaAprobador actualizado o None si no existe
            
        Raises:
            IntegrityError: Si hay un error de integridad
        """
        db_etapa_aprobador = self.get_by_id(etapa_aprobador_id)
        if not db_etapa_aprobador:
            return None
        
        # Actualizar solo los campos proporcionados
        update_data = etapa_aprobador_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_etapa_aprobador, field, value)
        
        self.db.commit()
        self.db.refresh(db_etapa_aprobador)
        
        # Recargar con relaciones
        return self.get_by_id(db_etapa_aprobador.id, include_relations=True)
    
    def delete(self, etapa_aprobador_id: int) -> bool:
        """
        Eliminar un etapa aprobador
        
        Args:
            etapa_aprobador_id: ID del etapa aprobador a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        db_etapa_aprobador = self.get_by_id(etapa_aprobador_id)
        if not db_etapa_aprobador:
            return False
        
        self.db.delete(db_etapa_aprobador)
        self.db.commit()
        return True
    
    def get_aprobadores_by_etapa(self, etapa_id: int, only_active: bool = True) -> List[EtapaAprobador]:
        """
        Obtener todos los aprobadores de una etapa
        
        Args:
            etapa_id: ID de la etapa
            only_active: Si True, solo retorna aprobadores activos
            
        Returns:
            Lista de aprobadores de la etapa
        """
        query = self.db.query(EtapaAprobador).options(
            joinedload(EtapaAprobador.user)
        ).filter(EtapaAprobador.etapa_id == etapa_id)
        
        if only_active:
            query = query.filter(EtapaAprobador.is_active == True)
        
        return query.all()
    
    def get_etapas_by_usuario(self, user_id: int, only_active: bool = True) -> List[EtapaAprobador]:
        """
        Obtener todas las etapas donde el usuario es aprobador
        
        Args:
            user_id: ID del usuario
            only_active: Si True, solo retorna asignaciones activas
            
        Returns:
            Lista de etapas donde el usuario es aprobador
        """
        query = self.db.query(EtapaAprobador).options(
            joinedload(EtapaAprobador.etapa)
        ).filter(EtapaAprobador.user_id == user_id)
        
        if only_active:
            query = query.filter(EtapaAprobador.is_active == True)
        
        return query.all()
