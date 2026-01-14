"""
Excepciones personalizadas para la aplicación
"""
from fastapi import HTTPException, status


class UnauthorizedException(HTTPException):
    """Excepción para errores de autenticación"""
    
    def __init__(self, detail: str = "No autorizado"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class BadRequestException(HTTPException):
    """Excepción para solicitudes malformadas"""
    
    def __init__(self, detail: str = "Solicitud incorrecta"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class NotFoundException(HTTPException):
    """Excepción para recursos no encontrados"""
    
    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class ForbiddenException(HTTPException):
    """Excepción para acceso prohibido"""
    
    def __init__(self, detail: str = "Acceso prohibido"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ConflictException(HTTPException):
    """Excepción para conflictos (ej: duplicados)"""
    
    def __init__(self, detail: str = "Conflicto con recurso existente"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )
