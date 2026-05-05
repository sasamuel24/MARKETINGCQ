"""
Schemas Pydantic para Iniciativas de Producto
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from db.models import IniciativaStatus


# ── Schemas de Usuario embebido (lectura) ──────────────────────────────────

class UserBasicResponse(BaseModel):
    id: int
    full_name: str
    email: str

    model_config = {"from_attributes": True}


# ── Create ─────────────────────────────────────────────────────────────────

class IniciativaCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=255)
    producto_propuesto: str = Field(..., min_length=1)
    analisis_competencia: Optional[str] = None
    descripcion: Optional[str] = None


# ── Update (BORRADOR) ──────────────────────────────────────────────────────

class IniciativaUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=255)
    producto_propuesto: Optional[str] = Field(None, min_length=1)
    analisis_competencia: Optional[str] = None
    descripcion: Optional[str] = None


# ── Acciones ───────────────────────────────────────────────────────────────

class IniciativaAprobarGGRequest(BaseModel):
    comment: Optional[str] = Field(None, max_length=1000)


class IniciativaRechazarRequest(BaseModel):
    comment: str = Field(..., min_length=1, max_length=1000)


class IniciativaAprobarDualRequest(BaseModel):
    comment: Optional[str] = Field(None, max_length=1000)


class TokenApprovalRequest(BaseModel):
    action: str = Field(..., pattern="^(APROBADO|RECHAZADO)$")
    comment: Optional[str] = Field(None, max_length=1000)


# ── Responses ──────────────────────────────────────────────────────────────

class IniciativaResponse(BaseModel):
    id: int
    titulo: str
    producto_propuesto: str
    analisis_competencia: Optional[str]
    descripcion: Optional[str]
    business_case_path: Optional[str]
    status: IniciativaStatus
    luisa_approved: bool
    gerente_tiendas_approved: bool
    created_by_user_id: int
    approved_by_gg_user_id: Optional[int]
    solicitud_id: Optional[int]
    solicitud_innovacion_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IniciativaDetailResponse(IniciativaResponse):
    created_by: Optional[UserBasicResponse] = None
    approved_by_gg: Optional[UserBasicResponse] = None


class IniciativaListResponse(BaseModel):
    iniciativas: list[IniciativaDetailResponse]
    total: int
    page: int
    page_size: int
