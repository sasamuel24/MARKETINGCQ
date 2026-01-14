"""
Schemas para roles - Validación con Pydantic
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class RoleBase(BaseModel):
    """Schema base para Role"""
    nombre: str = Field(..., min_length=1, max_length=120, description="Nombre del rol")


class RoleCreate(RoleBase):
    """Schema para crear un rol"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Administrador"
            }
        }
    )


class RoleUpdate(BaseModel):
    """Schema para actualizar un rol"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=120, description="Nombre del rol")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Editor"
            }
        }
    )


class RoleResponse(RoleBase):
    """Schema para respuesta de rol"""
    id: int = Field(..., description="ID del rol")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de actualización")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "nombre": "Administrador",
                "created_at": "2026-01-14T12:00:00",
                "updated_at": "2026-01-14T12:00:00"
            }
        }
    )


class RoleListResponse(BaseModel):
    """Schema para lista de roles con paginación"""
    roles: list[RoleResponse] = Field(..., description="Lista de roles")
    total: int = Field(..., description="Total de roles")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "roles": [
                    {
                        "id": 1,
                        "nombre": "Administrador",
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
