"""
Schemas para solicitud_files - Validación con Pydantic
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SolicitudInFile(BaseModel):
    """Schema simplificado de solicitud dentro de archivo"""
    id: int
    title: str
    
    model_config = ConfigDict(from_attributes=True)


class SolicitudFileBase(BaseModel):
    """Schema base para SolicitudFile"""
    storage_provider: str = Field(..., min_length=1, max_length=50, description="Proveedor de almacenamiento (s3, local, gcs)")
    storage_path: str = Field(..., min_length=1, max_length=500, description="Ruta completa del archivo en el storage")
    filename: str = Field(..., min_length=1, max_length=255, description="Nombre original del archivo")
    content_type: str = Field(..., min_length=1, max_length=100, description="Tipo MIME del archivo")
    size_bytes: int = Field(..., ge=0, description="Tamaño del archivo en bytes")
    doc_type: str = Field(..., min_length=1, max_length=50, description="Tipo de documento (ARTE, BRIEF, EVIDENCIA, etc.)")


class SolicitudFileCreate(SolicitudFileBase):
    """Schema para crear un archivo de solicitud"""
    solicitud_id: int = Field(..., gt=0, description="ID de la solicitud")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "solicitud_id": 1,
                "storage_provider": "s3",
                "storage_path": "bucket/solicitudes/2026/01/file123.pdf",
                "filename": "arte_campana_verano.pdf",
                "content_type": "application/pdf",
                "size_bytes": 2048576,
                "doc_type": "ARTE"
            }
        }
    )


class SolicitudFileUpdate(BaseModel):
    """Schema para actualizar un archivo de solicitud"""
    filename: Optional[str] = Field(None, min_length=1, max_length=255, description="Nombre original del archivo")
    doc_type: Optional[str] = Field(None, min_length=1, max_length=50, description="Tipo de documento")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "filename": "arte_campana_verano_v2.pdf",
                "doc_type": "ARTE_FINAL"
            }
        }
    )


class SolicitudFileResponse(SolicitudFileBase):
    """Schema para respuesta de archivo de solicitud"""
    id: int = Field(..., description="ID del archivo")
    solicitud_id: int = Field(..., description="ID de la solicitud")
    created_at: datetime = Field(..., description="Fecha de creación")
    updated_at: datetime = Field(..., description="Fecha de actualización")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "solicitud_id": 1,
                "storage_provider": "s3",
                "storage_path": "bucket/solicitudes/2026/01/file123.pdf",
                "filename": "arte_campana_verano.pdf",
                "content_type": "application/pdf",
                "size_bytes": 2048576,
                "doc_type": "ARTE",
                "created_at": "2026-01-15T10:00:00",
                "updated_at": "2026-01-15T10:00:00"
            }
        }
    )


class SolicitudFileDetailResponse(SolicitudFileResponse):
    """Schema para respuesta detallada de archivo con relaciones"""
    solicitud: SolicitudInFile = Field(..., description="Información de la solicitud")
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "solicitud_id": 1,
                "storage_provider": "s3",
                "storage_path": "bucket/solicitudes/2026/01/file123.pdf",
                "filename": "arte_campana_verano.pdf",
                "content_type": "application/pdf",
                "size_bytes": 2048576,
                "doc_type": "ARTE",
                "created_at": "2026-01-15T10:00:00",
                "updated_at": "2026-01-15T10:00:00",
                "solicitud": {
                    "id": 1,
                    "title": "Solicitud de arte para campaña Q1"
                }
            }
        }
    )


class SolicitudFileListResponse(BaseModel):
    """Schema para respuesta de lista de archivos"""
    total: int = Field(..., description="Total de registros")
    items: list[SolicitudFileDetailResponse] = Field(..., description="Lista de archivos")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1,
                "items": [
                    {
                        "id": 1,
                        "solicitud_id": 1,
                        "storage_provider": "s3",
                        "storage_path": "bucket/solicitudes/2026/01/file123.pdf",
                        "filename": "arte_campana_verano.pdf",
                        "content_type": "application/pdf",
                        "size_bytes": 2048576,
                        "doc_type": "ARTE",
                        "created_at": "2026-01-15T10:00:00",
                        "updated_at": "2026-01-15T10:00:00",
                        "solicitud": {
                            "id": 1,
                            "title": "Solicitud de arte para campaña Q1"
                        }
                    }
                ]
            }
        }
    )
