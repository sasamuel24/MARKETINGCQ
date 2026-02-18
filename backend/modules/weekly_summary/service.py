"""
Servicio de resumen semanal - Lógica de negocio.
Orquesta la obtención de solicitudes pendientes y el envío de correos.
"""
import logging
from sqlalchemy.orm import Session

from core.email import email_service
from modules.weekly_summary.repository import (
    get_pending_solicitudes_for_user,
    get_user_by_id,
)

logger = logging.getLogger(__name__)


class WeeklySummaryService:
    """Servicio para generar y enviar el resumen semanal de artes pendientes."""

    def run_for_users(self, db: Session, user_ids: list[int]) -> dict:
        """
        Ejecuta el envío del resumen semanal para los usuarios indicados.
        Procesa cada usuario de forma independiente para que un error en uno
        no bloquee al otro.
        
        Args:
            db: Sesión de base de datos
            user_ids: Lista de IDs de usuarios objetivo
            
        Returns:
            Diccionario con resumen del resultado por usuario
        """
        results = {}
        for user_id in user_ids:
            try:
                result = self._process_user(db, user_id)
                results[user_id] = result
            except Exception as e:
                logger.error(
                    f"[WeeklySummary] Error procesando usuario {user_id}: {e}",
                    exc_info=True,
                )
                results[user_id] = {"status": "error", "detail": str(e)}
        return results

    def _process_user(self, db: Session, user_id: int) -> dict:
        """
        Procesa un usuario individual: obtiene sus solicitudes pendientes
        y envía el correo si hay alguna.
        
        Args:
            db: Sesión de base de datos
            user_id: ID del usuario
            
        Returns:
            Diccionario con el resultado del procesamiento
        """
        usuario = get_user_by_id(db, user_id)
        if not usuario:
            logger.warning(f"[WeeklySummary] Usuario {user_id} no encontrado. Saltando.")
            return {"status": "skipped", "detail": "Usuario no encontrado"}

        solicitudes = get_pending_solicitudes_for_user(db, user_id)

        if not solicitudes:
            logger.info(
                f"[WeeklySummary] Usuario {usuario.full_name} (id={user_id}) "
                f"no tiene solicitudes pendientes. No se envía correo."
            )
            return {
                "status": "skipped",
                "detail": "Sin solicitudes pendientes",
                "user": usuario.full_name,
            }

        logger.info(
            f"[WeeklySummary] Enviando resumen a {usuario.email} "
            f"con {len(solicitudes)} solicitudes pendientes."
        )
        
        sent = email_service.send_weekly_summary_email(
            recipient_email=usuario.email,
            recipient_name=usuario.full_name,
            solicitudes=solicitudes,
        )
        
        return {
            "status": "sent" if sent else "email_failed",
            "user": usuario.full_name,
            "email": usuario.email,
            "solicitudes_count": len(solicitudes),
        }


# Instancia global del servicio
weekly_summary_service = WeeklySummaryService()
