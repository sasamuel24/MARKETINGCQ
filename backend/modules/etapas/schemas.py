"""
Schemas para etapas - Validación con Pydantic
"""
from typing import Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict


class ApprovalModeEnum(str, Enum):
    """Enum para el modo de aprobación"""
    ANY = "ANY"
    ALL = "ALL"


class AreaInEtapa(BaseModel):
    """Schema simplificado de área dentro de etapa"""
    id: int
    nombre: str
    
    model_config = ConfigDict(from_attributes=True)


class EtapaBase(BaseModel):
    """Schema base para Etapa"""
    code: str = Field(..., min_length=1, max_length=50, description="Código de la etapa")
    label: str = Field(..., min_length=1, max_length=120, description="Etiqueta visible de la etapa")
    order: int = Field(..., ge=0, description="Orden de la etapa en el flujo")


class EtapaCreate(EtapaBase):
    """Schema para crear una etapa"""
    area_id: int = Field(..., gt=0, description="ID del área")
    is_active: bool = Field(default=True, description="Indica si la etapa está activa")
    approval_mode: ApprovalModeEnum = Field(default=ApprovalModeEnum.ANY, description="Modo de aprobación")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "area_id": 1,
                "code": "PRIMER_FILTRO",
                "label": "Primer filtro",
                "order": 1,
                "is_active": True,
                "approval_mode": "ANY"
            }
        }
    )


class EtapaUpdate(BaseModel):
    """Schema para actualizar una etapa"""
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="Código de la etapa")
    label: Optional[str] = Field(None, min_length=1, max_length=120, description="Etiqueta visible de la etapa")
    order: Optional[int] = Field(None, ge=0, description="Orden de la etapa en el flujo")
    is_active: Optional[bool] = Field(None, description="Indica si la etapa está activa")
    approval_mode: Optional[ApprovalModeEnum] = Field(None, description="Modo de aprobación")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "label": "Primer filtro actualizado",
                "is_active": True
            }
        }
    )


class EtapaResponse(EtapaBase):
    """Schema para respuesta de etapa"""
    id: int = Field(..., description="ID de la etapa")
    area_id: int = Field(..., description="ID del área")
    is_active: bool = Field(..., description="Indica si la etapa está activa")
    approval_mode: ApprovalModeEnum = Field(..., description="Modo de aprobación")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de actualización")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "area_id": 1,
                "code": "PRIMER_FILTRO",
                "label": "Primer filtro",
                "order": 1,
                "is_active": True,
                "approval_mode": "ANY",
                "created_at": "2026-01-14T12:00:00",
                "updated_at": "2026-01-14T12:00:00"
            }
        }
    )


class EtapaDetailResponse(EtapaResponse):
    """Schema para respuesta detallada de etapa con área"""
    area: AreaInEtapa = Field(..., description="Información del área")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "area_id": 1,
                "code": "PRIMER_FILTRO",
                "label": "Primer filtro",
                "order": 1,
                "is_active": True,
                "approval_mode": "ANY",
                "area": {"id": 1, "nombre": "Marketing Digital"},
                "created_at": "2026-01-14T12:00:00",
                "updated_at": "2026-01-14T12:00:00"
            }
        }
    )


class EtapaListResponse(BaseModel):
    """Schema para lista de etapas con paginación"""
    etapas: list[EtapaDetailResponse] = Field(..., description="Lista de etapas")
    total: int = Field(..., description="Total de etapas")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "etapas": [
                    {
                        "id": 1,
                        "area_id": 1,
                        "code": "PRIMER_FILTRO",
                        "label": "Primer filtro",
                        "order": 1,
                        "is_active": True,
                        "approval_mode": "ANY",
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
