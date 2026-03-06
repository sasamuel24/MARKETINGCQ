"""
Schemas de autenticación (request/response models con Pydantic)
"""
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request body para login"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, description="Contraseña")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }
    }


class TokenResponse(BaseModel):
    """Response con tokens JWT"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Tipo de token")
    expires_in: int = Field(..., description="Segundos hasta expiración")
    must_change_password: bool = Field(default=False, description="Si el usuario debe cambiar su contraseña")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "must_change_password": False
            }
        }
    }


class RefreshTokenRequest(BaseModel):
    """Request para refrescar token"""
    refresh_token: str = Field(..., description="Refresh token")


class UserResponse(BaseModel):
    """Response con información del usuario"""
    id: str = Field(..., description="ID del usuario")
    email: str = Field(..., description="Email del usuario")
    full_name: Optional[str] = Field(None, description="Nombre completo")
    role: str = Field(..., description="Rol del usuario")
    rol_id: Optional[int] = Field(None, description="ID del rol del usuario")
    area_id: Optional[int] = Field(None, description="ID del área del usuario")
    is_active: bool = Field(default=True, description="Si el usuario está activo")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "1",
                "email": "user@example.com",
                "full_name": "Juan Pérez",
                "role": "user",
                "is_active": True
            }
        }
    }


class ChangePasswordRequest(BaseModel):
    """Request para cambiar contraseña"""
    new_password: str = Field(..., min_length=8, description="Nueva contraseña (mínimo 8 caracteres)")


class RegisterRequest(BaseModel):
    """Request para registrar nuevo usuario"""
    email: EmailStr = Field(..., description="Email del usuario")
    password: str = Field(..., min_length=6, description="Contraseña")
    full_name: Optional[str] = Field(None, description="Nombre completo")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "newuser@example.com",
                "password": "securepass123",
                "full_name": "Juan Pérez"
            }
        }
    }
