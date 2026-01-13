"""
Router de autenticación - Endpoints para login, refresh, me
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from modules.auth.schemas import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse
)
from modules.auth.service import AuthService
from core.dependencies import get_current_user_id
from core.exceptions import UnauthorizedException


router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(credentials: LoginRequest):
    """
    Login de usuario - Retorna access y refresh tokens
    
    - **email**: Email del usuario
    - **password**: Contraseña
    """
    auth_service = AuthService()
    
    # Autenticar usuario
    user = auth_service.authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    
    # Crear tokens
    tokens = auth_service.create_tokens(user["id"])
    
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refrescar access token usando refresh token
    
    - **refresh_token**: Token de refresco válido
    """
    auth_service = AuthService()
    
    try:
        tokens = auth_service.refresh_access_token(request.refresh_token)
        return TokenResponse(**tokens)
    except UnauthorizedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.detail)
        )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_current_user(
    user_id: Annotated[str, Depends(get_current_user_id)]
):
    """
    Obtener información del usuario autenticado actual
    
    Requiere JWT token válido en header Authorization: Bearer <token>
    """
    auth_service = AuthService()
    
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return UserResponse(**user)
