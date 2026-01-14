"""
Router de health check - Endpoint para verificar estado de la API
"""
from fastapi import APIRouter, status
from sqlalchemy import text
from datetime import datetime

from db.session import get_db


router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint - Verificar que la API está funcionando
    
    Returns:
        Estado de la API y timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "MarketingCQ API"
    }


@router.get("/db", status_code=status.HTTP_200_OK)
async def health_check_db():
    """
    Health check de base de datos - Verificar conectividad con PostgreSQL
    
    Returns:
        Estado de la conexión a base de datos
    """
    try:
        db = next(get_db())
        # Ejecutar una consulta simple para verificar la conexión
        db.execute(text("SELECT 1"))
        db.close()
        
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
