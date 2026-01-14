"""
Schemas para áreas - Validación con Pydantic
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AreaBase(BaseModel):
    """Schema base para Area"""
    nombre: str = Field(..., min_length=1, max_length=120, description="Nombre del área")


class AreaCreate(AreaBase):
    """Schema para crear un área"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Marketing Digital"
            }
        }
    )


class AreaUpdate(BaseModel):
    """Schema para actualizar un área"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=120, description="Nombre del área")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nombre": "Marketing y Comunicaciones"
            }
        }
    )


class AreaResponse(AreaBase):
    """Schema para respuesta de área"""
    id: int = Field(..., description="ID del área")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de actualización")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "nombre": "Marketing Digital",
                "created_at": "2026-01-14T12:00:00",
                "updated_at": "2026-01-14T12:00:00"
            }
        }
    )


class AreaListResponse(BaseModel):
    """Schema para lista de áreas con paginación"""
    areas: list[AreaResponse] = Field(..., description="Lista de áreas")
    total: int = Field(..., description="Total de áreas")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "areas": [
                    {
                        "id": 1,
                        "nombre": "Marketing Digital",
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
