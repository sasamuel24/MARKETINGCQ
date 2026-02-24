"""
Repositorio para operaciones con solicitudes en la base de datos
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from db.models import Solicitud, EtapaAprobador
from modules.solicitudes.schemas import SolicitudCreate, SolicitudUpdate


class SolicitudRepository:
    """Repositorio para gestionar operaciones CRUD de solicitudes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, solicitud_id: int, include_relations: bool = False) -> Optional[Solicitud]:
        """
        Obtener solicitud por ID
        
        Args:
            solicitud_id: ID de la solicitud
            include_relations: Si True, incluye área, etapa, estado, usuario creador y archivos
            
        Returns:
            Solicitud encontrada o None
        """
        query = self.db.query(Solicitud)
        if include_relations:
            query = query.options(
                joinedload(Solicitud.area),
                joinedload(Solicitud.stage),
                joinedload(Solicitud.state),
                joinedload(Solicitud.created_by),
                joinedload(Solicitud.files)
            )
        return query.filter(Solicitud.id == solicitud_id).first()
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        area_id: Optional[int] = None,
        stage_id: Optional[int] = None,
        status_id: Optional[int] = None,
        created_by_user_id: Optional[int] = None,
        approver_user_id: Optional[int] = None,
        include_relations: bool = True
    ) -> List[Solicitud]:
        """
        Obtener todas las solicitudes con paginación y filtros
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            area_id: Filtrar por área (opcional)
            stage_id: Filtrar por etapa (opcional)
            status_id: Filtrar por estado (opcional)
            created_by_user_id: Filtrar por usuario creador (opcional)
            approver_user_id: Filtrar por usuario aprobador (opcional)
            include_relations: Si True, incluye relaciones
            
        Returns:
            Lista de solicitudes ordenadas por created_at desc
        """
        query = self.db.query(Solicitud)
        if include_relations:
            query = query.options(
                joinedload(Solicitud.area),
                joinedload(Solicitud.stage),
                joinedload(Solicitud.state),
                joinedload(Solicitud.created_by),
                joinedload(Solicitud.files)
            )
        if area_id:
            query = query.filter(Solicitud.area_id == area_id)
        if stage_id:
            query = query.filter(Solicitud.stage_id == stage_id)
        if status_id:
            query = query.filter(Solicitud.status_id == status_id)
        if created_by_user_id:
            query = query.filter(Solicitud.created_by_user_id == created_by_user_id)
        if approver_user_id:
            query = query.join(EtapaAprobador, EtapaAprobador.etapa_id == Solicitud.stage_id)\
                         .filter(EtapaAprobador.user_id == approver_user_id)\
                         .filter(EtapaAprobador.is_active == True)
            # El usuario 10 (aprobador de café) solo ve solicitudes marcadas como café
            if approver_user_id == 10:
                query = query.filter(Solicitud.es_para_cafe == True)
        
        return query.order_by(Solicitud.created_at.desc()).offset(skip).limit(limit).all()
    
    def count(
        self,
        area_id: Optional[int] = None,
        stage_id: Optional[int] = None,
        status_id: Optional[int] = None,
        created_by_user_id: Optional[int] = None,
        approver_user_id: Optional[int] = None
    ) -> int:
        """
        Contar solicitudes con filtros
        
        Args:
            area_id: Filtrar por área (opcional)
            stage_id: Filtrar por etapa (opcional)
            status_id: Filtrar por estado (opcional)
            created_by_user_id: Filtrar por usuario creador (opcional)
            approver_user_id: Filtrar por usuario aprobador (opcional)
            
        Returns:
            Número de solicitudes
        """
        query = self.db.query(Solicitud)
        if area_id:
            query = query.filter(Solicitud.area_id == area_id)
        if stage_id:
            query = query.filter(Solicitud.stage_id == stage_id)
        if status_id:
            query = query.filter(Solicitud.status_id == status_id)
        if created_by_user_id:
            query = query.filter(Solicitud.created_by_user_id == created_by_user_id)
        if approver_user_id:
            query = query.join(EtapaAprobador, EtapaAprobador.etapa_id == Solicitud.stage_id)\
                         .filter(EtapaAprobador.user_id == approver_user_id)\
                         .filter(EtapaAprobador.is_active == True)
            # El usuario 10 (aprobador de café) solo ve solicitudes marcadas como café
            if approver_user_id == 10:
                query = query.filter(Solicitud.es_para_cafe == True)
        
        return query.count()
    
    def create(self, solicitud_data: SolicitudCreate, created_by_user_id: int) -> Solicitud:
        """
        Crear una nueva solicitud
        
        Args:
            solicitud_data: Datos de la solicitud
            created_by_user_id: ID del usuario que crea la solicitud
            
        Returns:
            Solicitud creada
            
        Raises:
            IntegrityError: Si hay un error de integridad (FK inválida, etc.)
        """
        db_solicitud = Solicitud(
            title=solicitud_data.title,
            description=solicitud_data.description,
            area_id=solicitud_data.area_id,
            stage_id=solicitud_data.stage_id,
            status_id=solicitud_data.status_id,
            created_by_user_id=created_by_user_id,
            es_para_cafe=solicitud_data.es_para_cafe
        )
        self.db.add(db_solicitud)
        self.db.commit()
        self.db.refresh(db_solicitud)
        
        # Recargar con relaciones
        return self.get_by_id(db_solicitud.id, include_relations=True)
    
    def update(self, solicitud_id: int, solicitud_data: SolicitudUpdate) -> Optional[Solicitud]:
        """
        Actualizar una solicitud existente
        
        Args:
            solicitud_id: ID de la solicitud a actualizar
            solicitud_data: Datos a actualizar
            
        Returns:
            Solicitud actualizada o None si no existe
            
        Raises:
            IntegrityError: Si hay un error de integridad
        """
        db_solicitud = self.get_by_id(solicitud_id)
        if not db_solicitud:
            return None
        
        # Actualizar solo los campos proporcionados
        update_data = solicitud_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_solicitud, field, value)
        
        self.db.commit()
        self.db.refresh(db_solicitud)
        
        # Recargar con relaciones
        return self.get_by_id(db_solicitud.id, include_relations=True)
    
    def delete(self, solicitud_id: int) -> bool:
        """
        Eliminar una solicitud
        
        Args:
            solicitud_id: ID de la solicitud a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        db_solicitud = self.get_by_id(solicitud_id)
        if not db_solicitud:
            return False
        
        self.db.delete(db_solicitud)
        self.db.commit()
        return True
    
    def get_by_area(self, area_id: int, include_relations: bool = True) -> List[Solicitud]:
        """
        Obtener todas las solicitudes de un área
        
        Args:
            area_id: ID del área
            include_relations: Si True, incluye relaciones
            
        Returns:
            Lista de solicitudes del área
        """
        query = self.db.query(Solicitud).filter(Solicitud.area_id == area_id)
        if include_relations:
            query = query.options(
                joinedload(Solicitud.area),
                joinedload(Solicitud.stage),
                joinedload(Solicitud.state),
                joinedload(Solicitud.created_by)
            )
        return query.order_by(Solicitud.created_at.desc()).all()
    
    def get_by_user(self, user_id: int, include_relations: bool = True) -> List[Solicitud]:
        """
        Obtener todas las solicitudes creadas por un usuario
        
        Args:
            user_id: ID del usuario
            include_relations: Si True, incluye relaciones
            
        Returns:
            Lista de solicitudes del usuario
        """
        query = self.db.query(Solicitud).filter(Solicitud.created_by_user_id == user_id)
        if include_relations:
            query = query.options(
                joinedload(Solicitud.area),
                joinedload(Solicitud.stage),
                joinedload(Solicitud.state),
                joinedload(Solicitud.created_by)
            )
        return query.order_by(Solicitud.created_at.desc()).all()
