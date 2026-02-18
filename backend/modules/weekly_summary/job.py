"""
Job de resumen semanal - Entry point para APScheduler.
Crea su propia sesión de DB (independiente del ciclo HTTP).
"""
import logging
from db.engine import SessionLocal
from core.config import settings
from modules.weekly_summary.service import weekly_summary_service

logger = logging.getLogger(__name__)


async def run_weekly_summary() -> None:
    """
    Entry point del job programado por APScheduler.
    Crea su propia sesión de DB, ejecuta el servicio
    y cierra la sesión al terminar.
    """
    logger.info("[WeeklySummary] ========== Iniciando job de resumen semanal ==========")
    db = SessionLocal()
    try:
        results = weekly_summary_service.run_for_users(
            db=db,
            user_ids=settings.WEEKLY_SUMMARY_USER_IDS,
        )
        logger.info(f"[WeeklySummary] Job completado. Resultados: {results}")
    except Exception as e:
        logger.error(f"[WeeklySummary] Error en job: {e}", exc_info=True)
    finally:
        db.close()
        logger.info("[WeeklySummary] ========== Job finalizado ==========")
