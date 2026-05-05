"""
Schemas Pydantic para Notificaciones internas
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificacionResponse(BaseModel):
    id: int
    user_id: int
    tipo: str
    titulo: str
    mensaje: str
    leida: bool
    iniciativa_id: Optional[int]
    solicitud_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificacionListResponse(BaseModel):
    notificaciones: list[NotificacionResponse]
    total: int
    no_leidas: int
