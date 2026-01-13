"""
Middlewares personalizados para logging, CORS, error handling, etc.
"""
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from core.config import settings


logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware para logging de requests HTTP
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Interceptar request, ejecutar, medir tiempo y loguear
        """
        start_time = time.time()
        
        # Info del request
        method = request.method
        url = request.url.path
        client_host = request.client.host if request.client else "unknown"
        
        # Ejecutar request
        response = await call_next(request)
        
        # Calcular tiempo de procesamiento
        process_time = time.time() - start_time
        
        # Loguear
        logger.info(
            f"{method} {url} - {response.status_code} - "
            f"{process_time:.3f}s - {client_host}"
        )
        
        # Agregar header con tiempo de procesamiento
        response.headers["X-Process-Time"] = str(process_time)
        
        return response


def setup_middlewares(app):
    """
    Configurar todos los middlewares de la aplicación
    
    Args:
        app: Instancia de FastAPI
    """
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request Logging Middleware
    if settings.DEBUG:
        app.add_middleware(RequestLoggingMiddleware)
