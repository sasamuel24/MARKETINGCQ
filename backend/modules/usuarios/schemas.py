"""
Schemas para usuarios - Validación con Pydantic
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# Schemas para relaciones anidadas
class RoleInUser(BaseModel):
    """Schema simplificado de rol dentro de usuario"""
    id: int
    nombre: str
    
    model_config = ConfigDict(from_attributes=True)


class AreaInUser(BaseModel):
    """Schema simplificado de área dentro de usuario"""
    id: int
    nombre: str
    
    model_config = ConfigDict(from_attributes=True)


# Schemas base
class UserBase(BaseModel):
    """Schema base para User"""
    full_name: str = Field(..., min_length=1, max_length=255, description="Nombre completo")
    email: EmailStr = Field(..., description="Email del usuario")


class UserCreate(UserBase):
    """Schema para crear un usuario"""
    password: str = Field(..., min_length=8, description="Contraseña (mínimo 8 caracteres)")
    rol_id: int = Field(..., gt=0, description="ID del rol")
    area_id: int = Field(..., gt=0, description="ID del área")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Juan Pérez",
                "email": "juan.perez@empresa.com",
                "password": "SecurePassword123",
                "rol_id": 1,
                "area_id": 1
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema para actualizar un usuario"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Nombre completo")
    email: Optional[EmailStr] = Field(None, description="Email del usuario")
    password: Optional[str] = Field(None, min_length=8, description="Nueva contraseña")
    rol_id: Optional[int] = Field(None, gt=0, description="ID del rol")
    area_id: Optional[int] = Field(None, gt=0, description="ID del área")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "Juan Pérez Actualizado",
                "email": "juan.nuevo@empresa.com"
            }
        }
    )


class UserResponse(UserBase):
    """Schema para respuesta de usuario (sin password_hash)"""
    id: int = Field(..., description="ID del usuario")
    rol_id: int = Field(..., description="ID del rol")
    area_id: int = Field(..., description="ID del área")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de actualización")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "full_name": "Juan Pérez",
                "email": "juan.perez@empresa.com",
                "rol_id": 1,
                "area_id": 1,
                "created_at": "2026-01-14T12:00:00",
                "updated_at": "2026-01-14T12:00:00"
            }
        }
    )


class UserDetailResponse(UserResponse):
    """Schema para respuesta detallada de usuario con relaciones"""
    rol: RoleInUser = Field(..., description="Información del rol")
    area: AreaInUser = Field(..., description="Información del área")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "full_name": "Juan Pérez",
                "email": "juan.perez@empresa.com",
                "rol_id": 1,
                "area_id": 1,
                "rol": {"id": 1, "nombre": "Administrador"},
                "area": {"id": 1, "nombre": "Marketing Digital"},
                "created_at": "2026-01-14T12:00:00",
                "updated_at": "2026-01-14T12:00:00"
            }
        }
    )


class UserListResponse(BaseModel):
    """Schema para lista de usuarios con paginación"""
    usuarios: list[UserDetailResponse] = Field(..., description="Lista de usuarios")
    total: int = Field(..., description="Total de usuarios")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "usuarios": [
                    {
                        "id": 1,
                        "full_name": "Juan Pérez",
                        "email": "juan.perez@empresa.com",
                        "rol_id": 1,
                        "area_id": 1,
                        "rol": {"id": 1, "nombre": "Administrador"},
                        "area": {"id": 1, "nombre": "Marketing Digital"},
                        "created_at": "2026-01-14T12:00:00",
                        "updated_at": "2026-01-14T12:00:00"
                    }
                ],
                "total": 1,
                "page": 1,
                "page_size": 10
            }
        }
    )
