"""
Router de Notificaciones - Endpoints REST
"""
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from modules.notificaciones.schemas import NotificacionListResponse, NotificacionResponse
from modules.notificaciones.repository import NotificacionRepository
from core.dependencies import get_current_user
from db.session import get_db

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


def get_repo(db: Session = Depends(get_db)) -> NotificacionRepository:
    return NotificacionRepository(db)


@router.get("", response_model=NotificacionListResponse)
async def get_notificaciones(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    solo_no_leidas: bool = Query(False),
    repo: NotificacionRepository = Depends(get_repo),
    current_user=Depends(get_current_user),
):
    """Obtener notificaciones del usuario autenticado"""
    skip = (page - 1) * page_size
    notificaciones, total, no_leidas = repo.get_by_user(
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        solo_no_leidas=solo_no_leidas,
    )
    return NotificacionListResponse(
        notificaciones=notificaciones,
        total=total,
        no_leidas=no_leidas,
    )


@router.put("/{notif_id}/marcar-leida", response_model=NotificacionResponse)
async def marcar_leida(
    notif_id: int,
    repo: NotificacionRepository = Depends(get_repo),
    current_user=Depends(get_current_user),
):
    """Marcar una notificación como leída"""
    notif = repo.marcar_leida(notif_id=notif_id, user_id=current_user.id)
    if not notif:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notificación no encontrada")
    return notif


@router.put("/marcar-todas-leidas", response_model=dict)
async def marcar_todas_leidas(
    repo: NotificacionRepository = Depends(get_repo),
    current_user=Depends(get_current_user),
):
    """Marcar todas las notificaciones del usuario como leídas"""
    updated = repo.marcar_todas_leidas(user_id=current_user.id)
    return {"updated": updated, "message": f"{updated} notificaciones marcadas como leídas"}
