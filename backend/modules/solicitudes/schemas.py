"""
Schemas para solicitudes - Validación con Pydantic
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FileInSolicitud(BaseModel):
    """Schema simplificado de archivo dentro de solicitud"""
    id: int
    filename: str
    content_type: str
    size_bytes: int
    doc_type: str
    storage_path: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AreaInSolicitud(BaseModel):
    """Schema simplificado de área dentro de solicitud"""
    id: int
    nombre: str
    
    model_config = ConfigDict(from_attributes=True)


class StageInSolicitud(BaseModel):
    """Schema simplificado de etapa (stage) dentro de solicitud"""
    id: int
    code: str
    label: str
    
    model_config = ConfigDict(from_attributes=True)


class StateInSolicitud(BaseModel):
    """Schema simplificado de estado (state) dentro de solicitud"""
    id: int
    code: str
    label: str
    
    model_config = ConfigDict(from_attributes=True)


class CreatedByInSolicitud(BaseModel):
    """Schema simplificado de usuario creador dentro de solicitud"""
    id: int
    full_name: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)


class SolicitudBase(BaseModel):
    """Schema base para Solicitud"""
    title: str = Field(..., min_length=1, max_length=255, description="Título de la solicitud")
    description: Optional[str] = Field(None, description="Descripción detallada de la solicitud")


class SolicitudCreate(SolicitudBase):
    """Schema para crear una solicitud"""
    area_id: int = Field(..., gt=0, description="ID del área")
    stage_id: int = Field(..., gt=0, description="ID de la etapa (stage)")
    status_id: int = Field(..., gt=0, description="ID del estado (state)")
    es_para_cafe: Optional[bool] = Field(None, description="Indica si el producto es para café (solo aplica en Operaciones y Calidad)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Solicitud de arte para campaña Q1",
                "description": "Necesitamos diseño para campaña de verano",
                "area_id": 1,
                "stage_id": 1,
                "status_id": 1
            }
        }
    )


class SolicitudUpdate(BaseModel):
    """Schema para actualizar una solicitud"""
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Título de la solicitud")
    description: Optional[str] = Field(None, description="Descripción detallada de la solicitud")
    stage_id: Optional[int] = Field(None, gt=0, description="ID de la etapa (stage)")
    status_id: Optional[int] = Field(None, gt=0, description="ID del estado (state)")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "Solicitud actualizada",
                "stage_id": 2,
                "status_id": 2
            }
        }
    )


class SolicitudAjusteRequest(BaseModel):
    """Schema para solicitar ajustes en una solicitud"""
    comment: str = Field(..., min_length=1, max_length=1000, description="Comentario explicando los ajustes necesarios")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comment": "Por favor ajustar los colores del logo y cambiar la tipografía del título"
            }
        }
    )


class SolicitudAprobarRequest(BaseModel):
    """Schema para aprobar una solicitud"""
    comment: Optional[str] = Field(None, max_length=1000, description="Comentario opcional al aprobar")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comment": "Aprobado. Todo está correcto."
            }
        }
    )


class SolicitudRechazarRequest(BaseModel):
    """Schema para rechazar una solicitud"""
    comment: str = Field(..., min_length=1, max_length=1000, description="Comentario explicando el motivo del rechazo")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "comment": "No cumple con los requisitos de marca establecidos"
            }
        }
    )


class SolicitudResponse(SolicitudBase):
    """Schema para respuesta de solicitud"""
    id: int = Field(..., description="ID de la solicitud")
    area_id: int = Field(..., description="ID del área")
    stage_id: int = Field(..., description="ID de la etapa")
    status_id: int = Field(..., description="ID del estado")
    created_by_user_id: int = Field(..., description="ID del usuario creador")
    es_para_cafe: Optional[bool] = Field(None, description="Indica si el producto es para café")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de actualización")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Solicitud de arte para campaña Q1",
                "description": "Necesitamos diseño para campaña de verano",
                "area_id": 1,
                "stage_id": 1,
                "status_id": 1,
                "created_by_user_id": 1,
                "created_at": "2026-01-15T10:00:00",
                "updated_at": "2026-01-15T10:00:00"
            }
        }
    )


class SolicitudDetailResponse(SolicitudResponse):
    """Schema para respuesta detallada de solicitud con relaciones"""
    area: AreaInSolicitud = Field(..., description="Información del área")
    stage: StageInSolicitud = Field(..., description="Información de la etapa")
    state: StateInSolicitud = Field(..., description="Información del estado")
    created_by: CreatedByInSolicitud = Field(..., description="Información del usuario creador")
    files: List[FileInSolicitud] = Field(default_factory=list, description="Archivos adjuntos")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Solicitud de arte para campaña Q1",
                "description": "Necesitamos diseño para campaña de verano",
                "area_id": 1,
                "stage_id": 1,
                "status_id": 1,
                "created_by_user_id": 1,
                "created_at": "2026-01-15T10:00:00",
                "updated_at": "2026-01-15T10:00:00",
                "area": {
                    "id": 1,
                    "nombre": "Marketing Digital"
                },
                "stage": {
                    "id": 1,
                    "code": "PRIMER_FILTRO",
                    "label": "Primer filtro"
                },
                "state": {
                    "id": 1,
                    "code": "PENDIENTE",
                    "label": "Pendiente"
                },
                "created_by": {
                    "id": 1,
                    "full_name": "Juan Pérez",
                    "email": "juan@example.com"
                }
            }
        }
    )


class SolicitudListResponse(BaseModel):
    """Schema para respuesta de lista de solicitudes"""
    total: int = Field(..., description="Total de registros")
    page: int = Field(..., description="Página actual")
    page_size: int = Field(..., description="Tamaño de página")
    solicitudes: list[SolicitudDetailResponse] = Field(..., description="Lista de solicitudes")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1,
                "page": 1,
                "page_size": 10,
                "solicitudes": [
                    {
                        "id": 1,
                        "title": "Solicitud de arte para campaña Q1",
                        "description": "Necesitamos diseño para campaña de verano",
                        "area_id": 1,
                        "stage_id": 1,
                        "status_id": 1,
                        "created_by_user_id": 1,
                        "created_at": "2026-01-15T10:00:00",
                        "updated_at": "2026-01-15T10:00:00",
                        "area": {
                            "id": 1,
                            "nombre": "Marketing Digital"
                        },
                        "stage": {
                            "id": 1,
                            "code": "PRIMER_FILTRO",
                            "label": "Primer filtro"
                        },
                        "state": {
                            "id": 1,
                            "code": "PENDIENTE",
                            "label": "Pendiente"
                        },
                        "created_by": {
                            "id": 1,
                            "full_name": "Juan Pérez",
                            "email": "juan@example.com"
                        }
                    }
                ]
            }
        }
    )
