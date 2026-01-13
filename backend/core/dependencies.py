"""
Dependencias reutilizables para FastAPI (autenticación, permisos, paginación, etc.)
"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from core.security import decode_token
from db.session import get_db


# Security scheme para JWT Bearer tokens
security = HTTPBearer()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> str:
    """
    Extraer y validar el user_id desde el JWT token
    
    Raises:
        HTTPException: Si el token es inválido o expiró
        
    Returns:
        user_id del token
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: Optional[str] = payload.get("sub")
    token_type: Optional[str] = payload.get("type")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar que sea un access token (no refresh token)
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token incorrecto",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


async def get_current_user(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Obtener el usuario completo desde la base de datos
    
    Nota: Este es un placeholder. En producción, deberías importar
    el modelo User y hacer la query real.
    
    Returns:
        User object
    """
    # TODO: Implementar cuando tengas el modelo User
    # from modules.users.models import User
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(status_code=404, detail="Usuario no encontrado")
    # return user
    
    # Por ahora, retornamos un dict simple
    return {
        "id": user_id,
        "email": "user@example.com",
        "is_active": True,
        "role": "user"
    }


class PaginationParams:
    """
    Parámetros de paginación reutilizables
    """
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20
    ):
        from core.config import settings
        
        # Validar página
        if page < 1:
            page = 1
            
        # Validar tamaño de página
        if page_size < 1:
            page_size = settings.DEFAULT_PAGE_SIZE
        elif page_size > settings.MAX_PAGE_SIZE:
            page_size = settings.MAX_PAGE_SIZE
            
        self.page = page
        self.page_size = page_size
        self.skip = (page - 1) * page_size
