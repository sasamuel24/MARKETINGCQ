"""
Punto de entrada de la aplicación FastAPI

Ejecutar con: uvicorn main:app --reload
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from core.config import settings
from core.middleware import setup_middlewares
from core.scheduler import setup_scheduler
from core.dependencies import get_current_user_id
from db.session import get_db

# Importar routers
from modules.auth.router import router as auth_router
from modules.health.router import router as health_router
from modules.roles.router import router as roles_router
from modules.areas.router import router as areas_router
from modules.usuarios.router import router as usuarios_router
from modules.estados.router import router as estados_router
from modules.etapas.router import router as etapas_router
from modules.etapa_aprobadores.router import router as etapa_aprobadores_router
from modules.solicitudes.router import router as solicitudes_router
from modules.solicitud_files.router import router as solicitud_files_router
from modules.iniciativas.router import router as iniciativas_router
from modules.notificaciones.router import router as notificaciones_router


# ── Lifespan: startup / shutdown ──
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    sched = setup_scheduler()
    sched.start()
    jobs = [j.name for j in sched.get_jobs()]
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    print(f"📚 Docs: http://localhost:{settings.PORT}/docs")
    print(f"🔗 API: http://localhost:{settings.PORT}{settings.API_PREFIX}")
    print(f"⏰ Scheduler iniciado. Jobs: {jobs}")
    
    yield  # La app corre aquí
    
    # SHUTDOWN
    sched.shutdown(wait=False)
    print("🔴 Scheduler detenido.")
    print("👋 Shutting down...")


# Crear instancia de FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para sistema de aprobación de artes de marketing",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Configurar middlewares (CORS, logging, etc.)
setup_middlewares(app)

# Registrar routers
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(roles_router, prefix=settings.API_PREFIX)
app.include_router(areas_router, prefix=settings.API_PREFIX)
app.include_router(usuarios_router, prefix=settings.API_PREFIX)
app.include_router(estados_router, prefix=settings.API_PREFIX)
app.include_router(etapas_router, prefix=settings.API_PREFIX)
app.include_router(etapa_aprobadores_router, prefix=settings.API_PREFIX)
app.include_router(solicitudes_router, prefix=settings.API_PREFIX)
app.include_router(solicitud_files_router, prefix=settings.API_PREFIX)
app.include_router(iniciativas_router, prefix=settings.API_PREFIX)
app.include_router(notificaciones_router, prefix=settings.API_PREFIX)


@app.post(
    f"{settings.API_PREFIX}/token-approval/{{token}}",
    tags=["Iniciativas"],
    summary="Aprobar/Rechazar vía Magic Link (sin login)",
)
async def token_approval(
    token: str,
    action: str,
    comment: str = "",
    db: Session = Depends(get_db),
):
    """
    Endpoint público para que el Gerente de Tiendas apruebe o rechace
    un prototipado sin necesidad de iniciar sesión.
    Acción: APROBADO | RECHAZADO
    """
    from modules.iniciativas.service import IniciativaService
    service = IniciativaService(db)
    return service.usar_token_aprobacion(token_str=token, action=action, comment=comment or None)


@app.get("/", include_in_schema=False)
async def root():
    """
    Redirigir a la documentación
    """
    return RedirectResponse(url="/docs")


@app.get("/api", include_in_schema=False)
async def api_root():
    """
    Información básica de la API
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": f"{settings.API_PREFIX}/health"
    }


# ── Endpoint admin: disparar resumen semanal manualmente ──
@app.post(
    f"{settings.API_PREFIX}/admin/trigger-weekly-summary",
    tags=["Admin"],
    summary="Disparar resumen semanal manualmente",
)
async def trigger_weekly_summary(
    current_user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Disparador manual del resumen semanal de artes pendientes.
    Útil para pruebas sin esperar al día programado.
    Requiere autenticación.
    """
    from modules.weekly_summary.service import weekly_summary_service

    results = weekly_summary_service.run_for_users(
        db=db,
        user_ids=settings.WEEKLY_SUMMARY_USER_IDS,
    )
    return {"message": "Resumen semanal ejecutado", "results": results}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
