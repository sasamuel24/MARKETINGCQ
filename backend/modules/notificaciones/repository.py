"""
Repositorio para operaciones con Notificaciones en la base de datos
"""
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from db.models import Notificacion


class NotificacionRepository:
    """Repositorio para gestionar notificaciones internas"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        solo_no_leidas: bool = False,
    ) -> Tuple[List[Notificacion], int, int]:
        query = self.db.query(Notificacion).filter(Notificacion.user_id == user_id)
        if solo_no_leidas:
            query = query.filter(Notificacion.leida == False)

        total = query.count()
        no_leidas = (
            self.db.query(Notificacion)
            .filter(Notificacion.user_id == user_id, Notificacion.leida == False)
            .count()
        )
        notificaciones = query.order_by(Notificacion.created_at.desc()).offset(skip).limit(limit).all()
        return notificaciones, total, no_leidas

    def create(
        self,
        user_id: int,
        tipo: str,
        titulo: str,
        mensaje: str,
        iniciativa_id: Optional[int] = None,
        solicitud_id: Optional[int] = None,
    ) -> Notificacion:
        notif = Notificacion(
            user_id=user_id,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            iniciativa_id=iniciativa_id,
            solicitud_id=solicitud_id,
            leida=False,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def marcar_leida(self, notif_id: int, user_id: int) -> Optional[Notificacion]:
        notif = (
            self.db.query(Notificacion)
            .filter(Notificacion.id == notif_id, Notificacion.user_id == user_id)
            .first()
        )
        if not notif:
            return None
        notif.leida = True
        self.db.commit()
        self.db.refresh(notif)
        return notif

    def marcar_todas_leidas(self, user_id: int) -> int:
        updated = (
            self.db.query(Notificacion)
            .filter(Notificacion.user_id == user_id, Notificacion.leida == False)
            .update({"leida": True})
        )
        self.db.commit()
        return updated
