"""
Servicio de autenticación - Lógica de negocio para auth
"""
from typing import Optional, Dict, Any
from datetime import timedelta

from core.config import settings
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from core.exceptions import UnauthorizedException, BadRequestException


class AuthService:
    """
    Servicio de autenticación con métodos para login, refresh, etc.
    
    Nota: Este es un ejemplo simplificado. En producción deberías:
    - Conectar con la base de datos real
    - Validar usuarios contra tabla Users
    - Manejar roles y permisos desde DB
    """
    
    # Mock de usuarios (reemplazar con DB en producción)
    MOCK_USERS = {
        "admin@marketingcq.com": {
            "id": "1",
            "email": "admin@marketingcq.com",
            "full_name": "Admin User",
            "hashed_password": get_password_hash("admin123"),
            "role": "admin",
            "is_active": True
        },
        "user@marketingcq.com": {
            "id": "2",
            "email": "user@marketingcq.com",
            "full_name": "Regular User",
            "hashed_password": get_password_hash("user123"),
            "role": "user",
            "is_active": True
        }
    }
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Autenticar usuario con email y password
        
        Args:
            email: Email del usuario
            password: Password en texto plano
            
        Returns:
            Usuario si las credenciales son válidas, None si no
        """
        user = self.MOCK_USERS.get(email)
        if not user:
            return None
        
        if not verify_password(password, user["hashed_password"]):
            return None
        
        if not user["is_active"]:
            return None
        
        return user
    
    def create_tokens(self, user_id: str) -> Dict[str, Any]:
        """
        Crear access y refresh tokens para un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con access_token, refresh_token, expires_in
        """
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Crear nuevo access token usando refresh token
        
        Args:
            refresh_token: Refresh token válido
            
        Returns:
            Dict con nuevo access_token
            
        Raises:
            UnauthorizedException: Si el refresh token es inválido
        """
        payload = decode_token(refresh_token)
        
        if not payload:
            raise UnauthorizedException("Refresh token inválido o expirado")
        
        # Verificar que sea un refresh token
        if payload.get("type") != "refresh":
            raise UnauthorizedException("Token inválido")
        
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException("Token inválido")
        
        # Crear nuevo access token
        access_token = create_access_token(data={"sub": user_id})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario si existe, None si no
        """
        for user in self.MOCK_USERS.values():
            if user["id"] == user_id:
                # No retornar el password
                return {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "role": user["role"],
                    "is_active": user["is_active"]
                }
        return None
