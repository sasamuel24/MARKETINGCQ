"""
Router de health check - Endpoints simples para verificar el estado del sistema
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime

from db.session import get_db
from core.config import settings


router = APIRouter(prefix="/health", tags=["Health Check"])


@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check básico - Verificar que la API está corriendo
    
    Returns:
        Dict con status y timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/db", status_code=status.HTTP_200_OK)
async def health_check_database(db: Session = Depends(get_db)):
    """
    Health check de base de datos - Verificar conectividad con PostgreSQL
    
    Returns:
        Dict con status de la base de datos
    """
    try:
        # Intentar ejecutar una query simple
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check - Verificar que el servicio está listo para recibir tráfico
    
    Verifica:
    - API corriendo
    - Database conectada
    
    Returns:
        Dict con estado de readiness
    """
    checks = {
        "api": "ready",
        "database": "unknown"
    }
    
    # Verificar database
    try:
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        checks["database"] = "ready"
    except Exception as e:
        checks["database"] = "not_ready"
        return {
            "status": "not_ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
