"""
Servicio de Iniciativas - Lógica de negocio del flujo de producto
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from db.models import (
    Iniciativa,
    IniciativaStatus,
    ApprovalTokenAction,
    User,
)
from modules.iniciativas.repository import IniciativaRepository
from modules.iniciativas.schemas import (
    IniciativaCreate,
    IniciativaUpdate,
    IniciativaDetailResponse,
    IniciativaListResponse,
)
from modules.notificaciones.repository import NotificacionRepository
from modules.usuarios.repository import UserRepository
from core.email import email_service
from core.config import settings


# IDs configurables (ajustar según BD real)
DIRECTOR_ROLE_NAME = "DIRECTOR"  # Nombre del rol de Director de Mercadeo
LUISA_USER_ID = 8          # Luisa Ibañez - calidad
GERENTE_TIENDAS_EMAIL = "prueba.gerenciatiendas@cafequindio.com.co"  # TODO: cambiar a email real en producción
GERENTE_TIENDAS_NAME = "Gerente de Tiendas"
JD_USER_IDS = [15]         # Directora de Mercadeo (directora@cafequindio.com.co) — aprueba paso a Innovación
AREA_4_CREATOR_USER_IDS = [2, 6]  # Creadores Área 4 (ajustar según BD)


class IniciativaService:
    """Servicio para gestionar el flujo de iniciativas de producto"""

    def __init__(self, db: Session):
        self.repository = IniciativaRepository(db)
        self.notif_repository = NotificacionRepository(db)
        self.user_repository = UserRepository(db)
        self.db = db

    # ── Consultas ──────────────────────────────────────────────────────────

    def get_by_id(self, iniciativa_id: int) -> IniciativaDetailResponse:
        iniciativa = self.repository.get_by_id(iniciativa_id)
        if not iniciativa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Iniciativa {iniciativa_id} no encontrada",
            )
        return IniciativaDetailResponse.model_validate(iniciativa)

    def _is_director(self, user: User) -> bool:
        """Verifica si el usuario tiene rol DIRECTOR"""
        return user.rol and user.rol.nombre == DIRECTOR_ROLE_NAME

    def get_all(
        self,
        page: int,
        page_size: int,
        current_user: User,
    ) -> IniciativaListResponse:
        skip = (page - 1) * page_size
        # DIRECTOR: solo ve sus propias iniciativas
        # CREATOR normal: solo ve sus propias iniciativas
        # APPROVER/ADMIN: ve todas
        is_director = self._is_director(current_user)
        # Creadores del Área 4 (prototipado/innovación): ven todas las iniciativas en flujo de prototipado
        is_area4_creator = (current_user.rol_id == 2 and getattr(current_user, 'area_id', None) == 4)
        if is_area4_creator:
            prototyping_statuses = [
                IniciativaStatus.APROBADA_GG,
                IniciativaStatus.EN_PROTOTIPADO,
                IniciativaStatus.PENDIENTE_APROBACION_DUAL,
                IniciativaStatus.PENDIENTE_JD,
                IniciativaStatus.APROBADA_JD,
            ]
            iniciativas, total = self.repository.get_all(skip=skip, limit=page_size, statuses=prototyping_statuses)
        else:
            created_by = current_user.id if (is_director or current_user.rol_id == 2) else None
            iniciativas, total = self.repository.get_all(skip=skip, limit=page_size, created_by_user_id=created_by)
        return IniciativaListResponse(
            iniciativas=[IniciativaDetailResponse.model_validate(i) for i in iniciativas],
            total=total,
            page=page,
            page_size=page_size,
        )

    # ── Crear ──────────────────────────────────────────────────────────────

    def crear(self, data: IniciativaCreate, current_user: User) -> IniciativaDetailResponse:
        if not self._is_director(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo la Directora de Mercadeo puede crear iniciativas",
            )
        iniciativa = self.repository.create(
            titulo=data.titulo,
            producto_propuesto=data.producto_propuesto,
            analisis_competencia=data.analisis_competencia,
            descripcion=data.descripcion,
            created_by_user_id=current_user.id,
        )
        return IniciativaDetailResponse.model_validate(iniciativa)

    # ── Editar (solo en BORRADOR) ──────────────────────────────────────────

    def editar(self, iniciativa_id: int, data: IniciativaUpdate, current_user: User) -> IniciativaDetailResponse:
        iniciativa = self._get_or_404(iniciativa_id)
        if iniciativa.status != IniciativaStatus.BORRADOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se puede editar una iniciativa en estado BORRADOR",
            )
        if iniciativa.created_by_user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para editar esta iniciativa")
        updates = data.model_dump(exclude_none=True)
        updated = self.repository.update_fields(iniciativa_id, **updates)
        return IniciativaDetailResponse.model_validate(updated)

    # ── Paso 1: Director envía directamente a Área 4 (Prototipado) ───────

    def enviar_a_gg(self, iniciativa_id: int, current_user: User) -> IniciativaDetailResponse:
        """Envía la iniciativa directamente al área de Producción/Bebidas (área 4) para prototipado."""
        iniciativa = self._get_or_404(iniciativa_id)
        if iniciativa.status != IniciativaStatus.BORRADOR:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Solo se puede enviar una iniciativa en estado BORRADOR",
            )
        if iniciativa.created_by_user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso")
        if not iniciativa.business_case_path:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debes adjuntar el Business Case antes de enviar a Prototipado",
            )

        # Salta directamente a APROBADA_GG (en espera de que Área 4 vincule la solicitud)
        updated = self.repository.update_fields(iniciativa_id, status=IniciativaStatus.APROBADA_GG)

        # Notificar directamente al Área 4 (Producción/Bebidas)
        area4_users = self._get_area4_creators()
        for u in area4_users:
            self.notif_repository.create(
                user_id=u.id,
                tipo="NUEVO_PROTOTIPADO",
                titulo=f"Nueva iniciativa para prototipado: {iniciativa.titulo}",
                mensaje=(
                    f"{current_user.full_name} envió una nueva iniciativa. "
                    f"Producto propuesto: {iniciativa.producto_propuesto}"
                ),
                iniciativa_id=iniciativa_id,
            )
        email_service.send_iniciativa_aprobada_area4_email(
            to_emails=[u.email for u in area4_users],
            iniciativa_id=iniciativa_id,
            iniciativa_titulo=iniciativa.titulo,
            producto_propuesto=iniciativa.producto_propuesto,
            gg_name=current_user.full_name,
        )
        return IniciativaDetailResponse.model_validate(updated)

    # ── Paso 2: GG aprueba ────────────────────────────────────────────────

    def aprobar_gg(self, iniciativa_id: int, comment: Optional[str], current_user: User) -> IniciativaDetailResponse:
        iniciativa = self._get_or_404(iniciativa_id)
        if iniciativa.status != IniciativaStatus.PENDIENTE_GG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La iniciativa no está en estado PENDIENTE_GG",
            )

        updated = self.repository.update_fields(
            iniciativa_id,
            status=IniciativaStatus.APROBADA_GG,
            approved_by_gg_user_id=current_user.id,
        )

        # Notificar al Director que fue aprobada
        self.notif_repository.create(
            user_id=iniciativa.created_by_user_id,
            tipo="INICIATIVA_APROBADA_GG",
            titulo=f"¡Iniciativa aprobada por Gerencia!: {iniciativa.titulo}",
            mensaje=f"{current_user.full_name} aprobó tu iniciativa. Se notificará al equipo de prototipado.",
            iniciativa_id=iniciativa_id,
        )

        # Notificar a Área 4 que deben iniciar prototipado
        area4_users = self._get_area4_creators()
        for u in area4_users:
            self.notif_repository.create(
                user_id=u.id,
                tipo="NUEVO_PROTOTIPADO",
                titulo=f"Nueva solicitud de prototipado: {iniciativa.titulo}",
                mensaje=(
                    f"La Gerencia General aprobó la iniciativa '{iniciativa.titulo}'. "
                    f"Deben crear el prototipado del producto: {iniciativa.producto_propuesto}"
                ),
                iniciativa_id=iniciativa_id,
            )
        email_service.send_iniciativa_aprobada_area4_email(
            to_emails=[u.email for u in area4_users],
            iniciativa_id=iniciativa_id,
            iniciativa_titulo=iniciativa.titulo,
            producto_propuesto=iniciativa.producto_propuesto,
            gg_name=current_user.full_name,
        )
        return IniciativaDetailResponse.model_validate(updated)

    # ── Paso 2b: GG rechaza ───────────────────────────────────────────────

    def rechazar_gg(self, iniciativa_id: int, comment: str, current_user: User) -> IniciativaDetailResponse:
        iniciativa = self._get_or_404(iniciativa_id)
        if iniciativa.status != IniciativaStatus.PENDIENTE_GG:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La iniciativa no está en estado PENDIENTE_GG",
            )
        updated = self.repository.update_fields(
            iniciativa_id,
            status=IniciativaStatus.RECHAZADA_GG,
            approved_by_gg_user_id=current_user.id,
        )
        self.notif_repository.create(
            user_id=iniciativa.created_by_user_id,
            tipo="INICIATIVA_RECHAZADA_GG",
            titulo=f"Iniciativa rechazada por Gerencia: {iniciativa.titulo}",
            mensaje=f"Motivo: {comment}",
            iniciativa_id=iniciativa_id,
        )
        return IniciativaDetailResponse.model_validate(updated)

    # ── Paso 3: Área 4 vincula su solicitud de prototipado ────────────────

    def vincular_solicitud_prototipado(
        self, iniciativa_id: int, solicitud_id: int, current_user: User
    ) -> IniciativaDetailResponse:
        iniciativa = self._get_or_404(iniciativa_id)
        if iniciativa.status not in (IniciativaStatus.APROBADA_GG, IniciativaStatus.EN_PROTOTIPADO):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La iniciativa debe estar en APROBADA_GG o EN_PROTOTIPADO para vincular prototipado",
            )
        updated = self.repository.update_fields(
            iniciativa_id,
            solicitud_id=solicitud_id,
            status=IniciativaStatus.EN_PROTOTIPADO,
        )
        return IniciativaDetailResponse.model_validate(updated)

    # ── Paso 4: Cierre diagnóstico activa aprobación dual ─────────────────

    def iniciar_aprobacion_dual(self, iniciativa_id: int, current_user: User) -> IniciativaDetailResponse:
        iniciativa = self._get_or_404(iniciativa_id)
        if iniciativa.status not in (IniciativaStatus.EN_PROTOTIPADO, IniciativaStatus.APROBADA_GG):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La iniciativa debe estar EN_PROTOTIPADO para iniciar aprobación dual",
            )

        updated = self.repository.update_fields(
            iniciativa_id,
            status=IniciativaStatus.PENDIENTE_APROBACION_DUAL,
            luisa_approved=False,
            gerente_tiendas_approved=False,
        )

        # Notificar a Luisa (en app + email normal)
        luisa = self.user_repository.get_by_id(LUISA_USER_ID)
        if luisa:
            self.notif_repository.create(
                user_id=LUISA_USER_ID,
                tipo="APROBACION_DUAL_PENDIENTE",
                titulo=f"Aprobación de prototipado requerida: {iniciativa.titulo}",
                mensaje="El prototipado está listo. Necesitas aprobar para continuar a Junta Directiva.",
                iniciativa_id=iniciativa_id,
            )
            email_service.send_dual_approval_luisa_email(
                to_email=luisa.email,
                iniciativa_id=iniciativa_id,
                iniciativa_titulo=iniciativa.titulo,
            )

        # Generar Magic Link para Gerente de Tiendas
        token = self.repository.create_approval_token(
            iniciativa_id=iniciativa_id,
            user_name=GERENTE_TIENDAS_NAME,
            user_email=GERENTE_TIENDAS_EMAIL,
            expires_hours=72,
        )
        email_service.send_magic_link_email(
            to_email=GERENTE_TIENDAS_EMAIL,
            to_name=GERENTE_TIENDAS_NAME,
            token=token.token,
            iniciativa_id=iniciativa_id,
            iniciativa_titulo=iniciativa.titulo,
            producto_propuesto=iniciativa.producto_propuesto,
        )

        return IniciativaDetailResponse.model_validate(updated)

    # ── Paso 5a: Luisa aprueba (dentro de la app) ─────────────────────────

    def aprobar_dual_luisa(self, iniciativa_id: int, comment: Optional[str], current_user: User) -> IniciativaDetailResponse:
        if current_user.id != LUISA_USER_ID:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo Luisa Ibañez puede aprobar en esta etapa")
        iniciativa = self._get_or_404(iniciativa_id)
        if iniciativa.status != IniciativaStatus.PENDIENTE_APROBACION_DUAL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La iniciativa no está en PENDIENTE_APROBACION_DUAL",
            )
        updated = self.repository.update_fields(iniciativa_id, luisa_approved=True)
        return self._check_dual_complete(iniciativa_id, updated)

    # ── Paso 5b: Gerente de Tiendas aprueba (Magic Link, sin login) ───────

    def usar_token_aprobacion(self, token_str: str, action: str, comment: Optional[str]) -> dict:
        token = self.repository.get_token(token_str)
        if not token:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token no encontrado")
        if token.action != ApprovalTokenAction.PENDIENTE:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Este token ya fue utilizado")
        if token.expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El token ha expirado")

        token_action = ApprovalTokenAction.APROBADO if action == "APROBADO" else ApprovalTokenAction.RECHAZADO
        self.repository.use_token(token, token_action, comment)

        iniciativa = self.repository.get_by_id(token.iniciativa_id)
        if not iniciativa:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Iniciativa no encontrada")

        if token_action == ApprovalTokenAction.APROBADO:
            updated = self.repository.update_fields(token.iniciativa_id, gerente_tiendas_approved=True)
            self._check_dual_complete(token.iniciativa_id, updated)
            return {"message": "Aprobación registrada exitosamente", "action": "APROBADO"}
        else:
            # Rechazo: vuelve a EN_PROTOTIPADO
            self.repository.update_fields(
                token.iniciativa_id,
                status=IniciativaStatus.EN_PROTOTIPADO,
                gerente_tiendas_approved=False,
                luisa_approved=False,
            )
            self.notif_repository.create(
                user_id=iniciativa.created_by_user_id,
                tipo="APROBACION_DUAL_RECHAZADA",
                titulo=f"Prototipado requiere ajustes: {iniciativa.titulo}",
                mensaje=f"El Gerente de Tiendas indicó: {comment or 'Sin comentario'}",
                iniciativa_id=token.iniciativa_id,
            )
            return {"message": "Rechazo registrado", "action": "RECHAZADO"}

    # ── Paso 6: JD aprueba ────────────────────────────────────────────────

    def aprobar_jd(self, iniciativa_id: int, comment: Optional[str], current_user: User) -> IniciativaDetailResponse:
        iniciativa = self._get_or_404(iniciativa_id)
        if iniciativa.status != IniciativaStatus.PENDIENTE_JD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La iniciativa no está en PENDIENTE_JD",
            )

        # ── Auto-crear solicitud en INNOVACION ─────────────────────────────
        solicitud_innovacion_id = None
        etapa_label = "Primera etapa"
        try:
            from db.models import Solicitud, Etapa

            # 1. Primera etapa del área INNOVACION (area_id=2)
            primera_etapa = (
                self.db.query(Etapa)
                .filter(Etapa.area_id == 2)
                .order_by(Etapa.order.asc())
                .first()
            )
            if not primera_etapa:
                raise ValueError("No se encontró ninguna etapa en el área INNOVACION")
            etapa_label = primera_etapa.label

            # 2. Primer CREATOR en INNOVACION (será created_by de la solicitud)
            creator_innovacion = (
                self.db.query(User)
                .filter(User.rol_id == 2, User.area_id == 2)
                .first()
            )
            if not creator_innovacion:
                raise ValueError("No hay usuarios CREATOR en el área INNOVACION")

            # 3. Crear la solicitud
            descripcion = (
                f"Solicitud generada automáticamente desde la Iniciativa de Producto aprobada por Junta Directiva.\n\n"
                f"Producto propuesto: {iniciativa.producto_propuesto}"
            )
            if iniciativa.analisis_competencia:
                descripcion += f"\n\nAnálisis de competencia: {iniciativa.analisis_competencia}"

            nueva_solicitud = Solicitud(
                title=f"[INNOVACIÓN] {iniciativa.titulo}",
                description=descripcion,
                area_id=2,
                stage_id=primera_etapa.id,
                status_id=1,  # EN_REVISION
                created_by_user_id=creator_innovacion.id,
            )
            self.db.add(nueva_solicitud)
            self.db.flush()  # obtener nueva_solicitud.id antes del commit
            solicitud_innovacion_id = nueva_solicitud.id
            logger.info(f"Solicitud INNOVACION {nueva_solicitud.id} creada automáticamente desde iniciativa {iniciativa_id}")

        except Exception as _e:
            logger.error(f"Error al auto-crear solicitud INNOVACION: {_e}")

        # ── Actualizar estado e IDs de la iniciativa ────────────────────────
        update_kwargs: dict = {"status": IniciativaStatus.APROBADA_JD}
        if solicitud_innovacion_id:
            update_kwargs["solicitud_innovacion_id"] = solicitud_innovacion_id
        self.db.commit()
        updated = self.repository.update_fields(iniciativa_id, **update_kwargs)

        # ── Notificar a todos los CREATORs de INNOVACION ───────────────────
        # La notificación lleva solo solicitud_id para que la campana lleve directo a la solicitud
        if solicitud_innovacion_id:
            try:
                creadores_innovacion = (
                    self.db.query(User)
                    .filter(User.rol_id == 2, User.area_id == 2)
                    .all()
                )
                for creador in creadores_innovacion:
                    self.notif_repository.create(
                        user_id=creador.id,
                        tipo="NUEVA_SOLICITUD_INNOVACION",
                        titulo=f"Nueva solicitud de Innovación: {iniciativa.titulo}",
                        mensaje=(
                            f"La iniciativa '{iniciativa.titulo}' fue aprobada por Junta Directiva. "
                            f"Se creó automáticamente la solicitud #{solicitud_innovacion_id} en tu área. "
                            f"Ingresa para comenzar el proceso."
                        ),
                        solicitud_id=solicitud_innovacion_id,  # solo solicitud_id → link directo a la solicitud
                    )
                    if creador.email:
                        try:
                            email_service.send_approval_notification(
                                to_emails=[creador.email],
                                solicitud_id=solicitud_innovacion_id,
                                solicitud_title=f"[INNOVACIÓN] {iniciativa.titulo}",
                                stage_name=etapa_label,
                                creator_name=iniciativa.titulo,
                            )
                        except Exception:
                            pass
            except Exception as _e:
                logger.warning(f"Error al notificar creadores INNOVACION: {_e}")

        # Notificar también al Director creador de la iniciativa
        self.notif_repository.create(
            user_id=iniciativa.created_by_user_id,
            tipo="INICIATIVA_APROBADA_JD",
            titulo=f"¡Junta Directiva aprobó la iniciativa!: {iniciativa.titulo}",
            mensaje=(
                f"La iniciativa fue aprobada. Se creó automáticamente la solicitud #{solicitud_innovacion_id} "
                f"en el área de Innovación para continuar el proceso."
            ) if solicitud_innovacion_id else (
                "La iniciativa fue aprobada. Por favor crea la solicitud correspondiente en el área de Innovación."
            ),
            iniciativa_id=iniciativa_id,
            solicitud_id=solicitud_innovacion_id,
        )
        return IniciativaDetailResponse.model_validate(updated)

    # ── Paso 6b: JD rechaza ───────────────────────────────────────────────

    def rechazar_jd(self, iniciativa_id: int, comment: str, current_user: User) -> IniciativaDetailResponse:
        iniciativa = self._get_or_404(iniciativa_id)
        if iniciativa.status != IniciativaStatus.PENDIENTE_JD:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La iniciativa no está en PENDIENTE_JD",
            )
        updated = self.repository.update_fields(iniciativa_id, status=IniciativaStatus.RECHAZADA_JD)
        self.notif_repository.create(
            user_id=iniciativa.created_by_user_id,
            tipo="INICIATIVA_RECHAZADA_JD",
            titulo=f"Iniciativa rechazada por Junta Directiva: {iniciativa.titulo}",
            mensaje=f"Motivo: {comment}",
            iniciativa_id=iniciativa_id,
        )
        return IniciativaDetailResponse.model_validate(updated)

    # ── Helpers privados ───────────────────────────────────────────────────

    def _get_or_404(self, iniciativa_id: int) -> Iniciativa:
        iniciativa = self.db.query(Iniciativa).filter(Iniciativa.id == iniciativa_id).first()
        if not iniciativa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Iniciativa {iniciativa_id} no encontrada",
            )
        return iniciativa

    def _check_dual_complete(self, iniciativa_id: int, iniciativa: Iniciativa) -> IniciativaDetailResponse:
        """Si ambos aprobaron, avanza a PENDIENTE_JD y auto-avanza la solicitud de prototipado a PROD_E3"""
        if iniciativa.luisa_approved and iniciativa.gerente_tiendas_approved:
            updated = self.repository.update_fields(iniciativa_id, status=IniciativaStatus.PENDIENTE_JD)

            # Auto-avanzar la solicitud vinculada de PROD_E2 → PROD_E3
            if iniciativa.solicitud_id:
                try:
                    from db.models import Solicitud, Etapa, EtapaAprobador
                    from modules.solicitudes.schemas import SolicitudUpdate
                    solicitud = self.db.query(Solicitud).filter(Solicitud.id == iniciativa.solicitud_id).first()
                    if solicitud:
                        etapa_actual = self.db.query(Etapa).filter(Etapa.id == solicitud.stage_id).first()
                        if etapa_actual and etapa_actual.code == "PROD_E2":
                            siguiente_etapa = self.db.query(Etapa).filter(
                                Etapa.area_id == solicitud.area_id,
                                Etapa.order == etapa_actual.order + 1,
                            ).first()
                            if siguiente_etapa:
                                solicitud.stage_id = siguiente_etapa.id
                                solicitud.status_id = 1  # EN_REVISION
                                self.db.commit()
                                # Notificar aprobadores de PROD_E3
                                aprobadores_e3 = self.db.query(EtapaAprobador).filter(
                                    EtapaAprobador.etapa_id == siguiente_etapa.id,
                                    EtapaAprobador.is_active == True,
                                ).all()
                                emails_e3 = []
                                for ap in aprobadores_e3:
                                    u = self.db.query(User).filter(User.id == ap.user_id).first()
                                    if u and u.email:
                                        emails_e3.append(u.email)
                                if emails_e3:
                                    email_service.send_approval_notification(
                                        to_emails=emails_e3,
                                        solicitud_id=solicitud.id,
                                        solicitud_title=solicitud.title,
                                        stage_name=siguiente_etapa.label,
                                        creator_name=iniciativa.titulo,
                                    )
                                logger.info(f"Solicitud {solicitud.id} avanzada automáticamente de PROD_E2 a PROD_E3 por aprobación dual completa")
                except Exception as _e:
                    logger.warning(f"No se pudo avanzar la solicitud tras aprobación dual: {_e}")

            # Notificar a JD
            jd_users = self._get_jd_users()
            for jd_user in jd_users:
                self.notif_repository.create(
                    user_id=jd_user.id,
                    tipo="INICIATIVA_PENDIENTE_JD",
                    titulo=f"Iniciativa pendiente de aprobación final: {iniciativa.titulo}",
                    mensaje="El prototipado fue aprobado. Requiere su aprobación para continuar.",
                    iniciativa_id=iniciativa_id,
                )
            email_service.send_jd_pending_email(
                to_emails=[u.email for u in jd_users],
                iniciativa_id=iniciativa_id,
                iniciativa_titulo=iniciativa.titulo,
            )
            return IniciativaDetailResponse.model_validate(updated)
        return IniciativaDetailResponse.model_validate(iniciativa)

    def _get_gg_users(self) -> list:
        """Usuarios de Gerencia General: APPROVERs en área INNOVACION (area_id=2)"""
        return (
            self.db.query(User)
            .filter(User.rol_id == 3, User.area_id == 2)
            .all()
        )

    def _get_area4_creators(self) -> list:
        """CREATORs del área 4 (Prototipado/Bebidas)"""
        return (
            self.db.query(User)
            .filter(User.rol_id == 2, User.area_id == 4)
            .all()
        )

    def _get_jd_users(self) -> list:
        """Usuarios de Junta Directiva"""
        return self.db.query(User).filter(User.id.in_(JD_USER_IDS)).all()
