"""
Repository para obtener solicitudes pendientes de aprobación por usuario.
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from db.models import Solicitud, EtapaAprobador, Estado, User

logger = logging.getLogger(__name__)


def get_pending_solicitudes_for_user(db: Session, user_id: int) -> List[Solicitud]:
    """
    Retorna solicitudes donde el usuario es aprobador de la etapa actual
    y la solicitud NO está en estado final ni rechazado/ajustes.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario aprobador
        
    Returns:
        Lista de solicitudes pendientes ordenadas por fecha de creación
    """
    return (
        db.query(Solicitud)
        .join(
            EtapaAprobador,
            (EtapaAprobador.etapa_id == Solicitud.stage_id)
            & (EtapaAprobador.user_id == user_id)
            & (EtapaAprobador.is_active == True),
        )
        .join(Estado, Solicitud.status_id == Estado.id)
        .options(
            joinedload(Solicitud.stage),
            joinedload(Solicitud.state),
            joinedload(Solicitud.area),
            joinedload(Solicitud.created_by),
        )
        .filter(Estado.is_final == False)
        .filter(Estado.code.notin_(["RECHAZADO", "AJUSTES_SOLICITADOS"]))
        .order_by(Solicitud.created_at.asc())
        .all()
    )


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Obtener usuario por ID.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario
        
    Returns:
        Usuario encontrado o None
    """
    return db.query(User).filter(User.id == user_id).first()
