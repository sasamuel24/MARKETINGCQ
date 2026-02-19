"""
Servicio de autenticación - Lógica de negocio para auth
"""
from typing import Optional, Dict, Any
from datetime import timedelta
from sqlalchemy.orm import Session

from core.config import settings
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from core.exceptions import UnauthorizedException, BadRequestException
from db.models import User
from db.session import SessionLocal


class AuthService:
    """
    Servicio de autenticación con métodos para login, refresh, etc.
    """
    
    def __init__(self, db: Session = None):
        """
        Args:
            db: Sesión de base de datos opcional
        """
        self.db = db or SessionLocal()
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Autenticar usuario con email y password
        
        Args:
            email: Email del usuario
            password: Password en texto plano
            
        Returns:
            Usuario si las credenciales son válidas, None si no
        """
        # Buscar usuario en la base de datos
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        
        # Verificar password
        if not verify_password(password, user.password_hash):
            return None
        
        # Retornar datos del usuario
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.rol.nombre if user.rol else "user",
            "rol_id": user.rol_id,
            "area_id": user.area_id,
            "must_change_password": user.must_change_password,
        }
    
    def create_tokens(self, user_id: str, must_change_password: bool = False) -> Dict[str, Any]:
        """
        Crear access y refresh tokens para un usuario
        
        Args:
            user_id: ID del usuario
            must_change_password: Si el usuario debe cambiar su contraseña
            
        Returns:
            Dict con access_token, refresh_token, expires_in, must_change_password
        """
        access_token = create_access_token(data={"sub": user_id})
        refresh_token = create_refresh_token(data={"sub": user_id})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "must_change_password": must_change_password,
        }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Crear nuevo access token usando refresh token
        
        Args:
            refresh_token: Refresh token válido
            
        Returns:
            Dict con nuevo access_token y refresh_token
            
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
        
        # Crear nuevo refresh token (opcional: puedes reutilizar el mismo)
        new_refresh_token = create_refresh_token(data={"sub": user_id})
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    
    def change_user_password(self, user_id: str, new_password: str) -> None:
        """
        Cambiar contraseña del usuario y marcar must_change_password = False
        
        Args:
            user_id: ID del usuario
            new_password: Nueva contraseña en texto plano
        """
        from fastapi import HTTPException
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        user.password_hash = get_password_hash(new_password)
        user.must_change_password = False
        self.db.commit()

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener usuario por ID
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Usuario si existe, None si no
        """
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            return None
        
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.rol.nombre if user.rol else "user",
            "rol_id": user.rol_id,
            "area_id": user.area_id
        }
