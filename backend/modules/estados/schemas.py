"""
Schemas para estados - Validación con Pydantic
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class EstadoBase(BaseModel):
    """Schema base para Estado"""
    code: str = Field(..., min_length=1, max_length=50, description="Código único del estado")
    label: str = Field(..., min_length=1, max_length=120, description="Etiqueta visible del estado")
    order: int = Field(..., ge=0, description="Orden del estado en el flujo")


class EstadoCreate(EstadoBase):
    """Schema para crear un estado"""
    is_final: bool = Field(default=False, description="Indica si es un estado final")
    is_active: bool = Field(default=True, description="Indica si el estado está activo")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "CREATED",
                "label": "Creado",
                "order": 1,
                "is_final": False,
                "is_active": True
            }
        }
    )


class EstadoUpdate(BaseModel):
    """Schema para actualizar un estado"""
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="Código único del estado")
    label: Optional[str] = Field(None, min_length=1, max_length=120, description="Etiqueta visible del estado")
    order: Optional[int] = Field(None, ge=0, description="Orden del estado en el flujo")
    is_final: Optional[bool] = Field(None, description="Indica si es un estado final")
    is_active: Optional[bool] = Field(None, description="Indica si el estado está activo")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "label": "En Revisión",
                "is_active": True
            }
        }
    )


class EstadoResponse(EstadoBase):
    """Schema para respuesta de estado"""
    id: int = Field(..., description="ID del estado")
    is_final: bool = Field(..., description="Indica si es un estado final")
    is_active: bool = Field(..., description="Indica si el estado está activo")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de actualización")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "code": "CREATED",
                "label": "Creado",
                "order": 1,
                "is_final": False,
                "is_active": True,
                "created_at": "2026-01-14T12:00:00",
                "updated_at": "2026-01-14T12:00:00"
            }
        }
    )


class EstadoListResponse(BaseModel):
    """Schema para lista de estados con paginación"""
    estados: list[EstadoResponse] = Field(..., description="Lista de estados")
    total: int = Field(..., description="Total de estados")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "estados": [
                    {
                        "id": 1,
                        "code": "CREATED",
                        "label": "Creado",
                        "order": 1,
                        "is_final": False,
                        "is_active": True,
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
