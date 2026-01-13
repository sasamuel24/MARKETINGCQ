"""
Punto de entrada de la aplicación FastAPI

Ejecutar con: uvicorn main:app --reload
"""
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from core.config import settings
from core.middleware import setup_middlewares

# Importar routers
from modules.auth.router import router as auth_router
from modules.health.router import router as health_router


# Crear instancia de FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API para sistema de aprobación de artes de marketing",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.DEBUG
)

# Configurar middlewares (CORS, logging, etc.)
setup_middlewares(app)

# Registrar routers
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(health_router, prefix=settings.API_PREFIX)


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


# Event handlers
@app.on_event("startup")
async def startup_event():
    """
    Ejecutar al iniciar la aplicación
    """
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    print(f"📚 Docs: http://localhost:{settings.PORT}/docs")
    print(f"🔗 API: http://localhost:{settings.PORT}{settings.API_PREFIX}")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Ejecutar al cerrar la aplicación
    """
    print("👋 Shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
