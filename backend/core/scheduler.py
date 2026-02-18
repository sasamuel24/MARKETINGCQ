"""
Configuración de APScheduler para tareas programadas.
Integrado directamente en el proceso de FastAPI.
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# Instancia global del scheduler (zona horaria de Colombia)
scheduler = AsyncIOScheduler(timezone="America/Bogota")


def setup_scheduler() -> AsyncIOScheduler:
    """
    Configura el scheduler con todos los jobs programados.
    
    Returns:
        AsyncIOScheduler configurado y listo para iniciar.
    """
    from core.config import settings

    if settings.WEEKLY_SUMMARY_ENABLED:
        from modules.weekly_summary.job import run_weekly_summary

        scheduler.add_job(
            func=run_weekly_summary,
            trigger=CronTrigger(
                day_of_week=settings.WEEKLY_CRON_DAY,
                hour=settings.WEEKLY_CRON_HOUR,
                minute=settings.WEEKLY_CRON_MINUTE,
            ),
            id="weekly_summary_email",
            name="Resumen semanal de artes pendientes",
            replace_existing=True,
            misfire_grace_time=3600,  # Si el server estuvo caído, ejecutar hasta 1h después
        )
        logger.info(
            f"[Scheduler] Job 'weekly_summary_email' programado: "
            f"{settings.WEEKLY_CRON_DAY} a las {settings.WEEKLY_CRON_HOUR}:{settings.WEEKLY_CRON_MINUTE:02d}"
        )
    else:
        logger.info("[Scheduler] Resumen semanal DESACTIVADO (WEEKLY_SUMMARY_ENABLED=false)")

    return scheduler
