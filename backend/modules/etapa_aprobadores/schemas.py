"""
Schemas para etapa_aprobadores - Validación con Pydantic
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class UsuarioInEtapaAprobador(BaseModel):
    """Schema simplificado de usuario dentro de etapa aprobador"""
    id: int
    full_name: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)


class EtapaInEtapaAprobador(BaseModel):
    """Schema simplificado de etapa dentro de etapa aprobador"""
    id: int
    code: str
    label: str
    
    model_config = ConfigDict(from_attributes=True)


class EtapaAprobadorBase(BaseModel):
    """Schema base para EtapaAprobador"""
    etapa_id: int = Field(..., gt=0, description="ID de la etapa")
    user_id: int = Field(..., gt=0, description="ID del usuario aprobador")


class EtapaAprobadorCreate(EtapaAprobadorBase):
    """Schema para crear un etapa aprobador"""
    is_active: bool = Field(default=True, description="Indica si la asignación está activa")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "etapa_id": 1,
                "user_id": 2,
                "is_active": True
            }
        }
    )


class EtapaAprobadorUpdate(BaseModel):
    """Schema para actualizar un etapa aprobador"""
    is_active: Optional[bool] = Field(None, description="Indica si la asignación está activa")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_active": False
            }
        }
    )


class EtapaAprobadorResponse(EtapaAprobadorBase):
    """Schema para respuesta de etapa aprobador"""
    id: int = Field(..., description="ID del registro")
    is_active: bool = Field(..., description="Indica si la asignación está activa")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de actualización")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "etapa_id": 1,
                "user_id": 2,
                "is_active": True,
                "created_at": "2026-01-15T10:00:00",
                "updated_at": "2026-01-15T10:00:00"
            }
        }
    )


class EtapaAprobadorDetailResponse(EtapaAprobadorResponse):
    """Schema para respuesta detallada de etapa aprobador con relaciones"""
    etapa: EtapaInEtapaAprobador = Field(..., description="Información de la etapa")
    user: UsuarioInEtapaAprobador = Field(..., description="Información del usuario aprobador")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "etapa_id": 1,
                "user_id": 2,
                "is_active": True,
                "created_at": "2026-01-15T10:00:00",
                "updated_at": "2026-01-15T10:00:00",
                "etapa": {
                    "id": 1,
                    "code": "PRIMER_FILTRO",
                    "label": "Primer filtro"
                },
                "user": {
                    "id": 2,
                    "full_name": "Juan Pérez",
                    "email": "juan@example.com"
                }
            }
        }
    )


class EtapaAprobadorListResponse(BaseModel):
    """Schema para respuesta de lista de etapas aprobadores"""
    total: int = Field(..., description="Total de registros")
    items: list[EtapaAprobadorDetailResponse] = Field(..., description="Lista de etapas aprobadores")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 2,
                "items": [
                    {
                        "id": 1,
                        "etapa_id": 1,
                        "user_id": 2,
                        "is_active": True,
                        "created_at": "2026-01-15T10:00:00",
                        "updated_at": "2026-01-15T10:00:00",
                        "etapa": {
                            "id": 1,
                            "code": "PRIMER_FILTRO",
                            "label": "Primer filtro"
                        },
                        "user": {
                            "id": 2,
                            "full_name": "Juan Pérez",
                            "email": "juan@example.com"
                        }
                    }
                ]
            }
        }
    )
