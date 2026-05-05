"""
Repositorio para operaciones con Iniciativas en la base de datos
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, List, Tuple

from sqlalchemy.orm import Session, joinedload

from db.models import Iniciativa, IniciativaStatus, ApprovalToken, ApprovalTokenAction


class IniciativaRepository:
    """Repositorio para gestionar operaciones CRUD de iniciativas"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, iniciativa_id: int) -> Optional[Iniciativa]:
        return (
            self.db.query(Iniciativa)
            .options(
                joinedload(Iniciativa.created_by),
                joinedload(Iniciativa.approved_by_gg),
            )
            .filter(Iniciativa.id == iniciativa_id)
            .first()
        )

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        created_by_user_id: Optional[int] = None,
        status: Optional[IniciativaStatus] = None,
        statuses: Optional[List[IniciativaStatus]] = None,
    ) -> Tuple[List[Iniciativa], int]:
        query = self.db.query(Iniciativa).options(
            joinedload(Iniciativa.created_by),
            joinedload(Iniciativa.approved_by_gg),
        )
        if created_by_user_id is not None:
            query = query.filter(Iniciativa.created_by_user_id == created_by_user_id)
        if statuses is not None:
            query = query.filter(Iniciativa.status.in_(statuses))
        elif status is not None:
            query = query.filter(Iniciativa.status == status)

        total = query.count()
        iniciativas = query.order_by(Iniciativa.created_at.desc()).offset(skip).limit(limit).all()
        return iniciativas, total

    def create(
        self,
        titulo: str,
        producto_propuesto: str,
        created_by_user_id: int,
        analisis_competencia: Optional[str] = None,
        descripcion: Optional[str] = None,
    ) -> Iniciativa:
        iniciativa = Iniciativa(
            titulo=titulo,
            producto_propuesto=producto_propuesto,
            analisis_competencia=analisis_competencia,
            descripcion=descripcion,
            created_by_user_id=created_by_user_id,
            status=IniciativaStatus.BORRADOR,
            luisa_approved=False,
            gerente_tiendas_approved=False,
        )
        self.db.add(iniciativa)
        self.db.commit()
        self.db.refresh(iniciativa)
        return self.get_by_id(iniciativa.id)

    def update_fields(self, iniciativa_id: int, **kwargs) -> Optional[Iniciativa]:
        iniciativa = self.db.query(Iniciativa).filter(Iniciativa.id == iniciativa_id).first()
        if not iniciativa:
            return None
        for key, value in kwargs.items():
            if hasattr(iniciativa, key):
                setattr(iniciativa, key, value)
        self.db.commit()
        self.db.refresh(iniciativa)
        return self.get_by_id(iniciativa_id)

    # ── ApprovalToken helpers ──────────────────────────────────────────────

    def create_approval_token(
        self,
        iniciativa_id: int,
        user_name: str,
        user_email: str,
        expires_hours: int = 72,
    ) -> ApprovalToken:
        token = ApprovalToken(
            token=str(uuid.uuid4()),
            iniciativa_id=iniciativa_id,
            user_name=user_name,
            user_email=user_email,
            action=ApprovalTokenAction.PENDIENTE,
            expires_at=datetime.utcnow() + timedelta(hours=expires_hours),
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_token(self, token_str: str) -> Optional[ApprovalToken]:
        return (
            self.db.query(ApprovalToken)
            .options(joinedload(ApprovalToken.iniciativa))
            .filter(ApprovalToken.token == token_str)
            .first()
        )

    def use_token(self, token: ApprovalToken, action: ApprovalTokenAction, comment: Optional[str]) -> ApprovalToken:
        token.action = action
        token.comment = comment
        token.used_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(token)
        return token
