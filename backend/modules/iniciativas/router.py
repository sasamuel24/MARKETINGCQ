"""
Router de Iniciativas - Endpoints REST para el flujo de iniciativa de producto
"""
import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse
from core.storage import get_s3_storage, S3StorageService
from sqlalchemy.orm import Session

from modules.iniciativas.schemas import (
    IniciativaCreate,
    IniciativaUpdate,
    IniciativaDetailResponse,
    IniciativaListResponse,
    IniciativaAprobarGGRequest,
    IniciativaRechazarRequest,
    IniciativaAprobarDualRequest,
    TokenApprovalRequest,
)
from modules.iniciativas.service import IniciativaService
from core.dependencies import get_current_user
from db.session import get_db

router = APIRouter(prefix="/iniciativas", tags=["Iniciativas"])


def get_service(db: Session = Depends(get_db)) -> IniciativaService:
    return IniciativaService(db)


# ── CRUD básico ────────────────────────────────────────────────────────────

@router.get("", response_model=IniciativaListResponse)
async def listar_iniciativas(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """Listar iniciativas. CREATOR: solo las propias. APPROVER/ADMIN: todas."""
    return service.get_all(page=page, page_size=page_size, current_user=current_user)


@router.get("/{iniciativa_id}", response_model=IniciativaDetailResponse)
async def obtener_iniciativa(
    iniciativa_id: int,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    return service.get_by_id(iniciativa_id)


@router.post("", response_model=IniciativaDetailResponse, status_code=status.HTTP_201_CREATED)
async def crear_iniciativa(
    data: IniciativaCreate,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """Crear una nueva iniciativa de producto (queda en BORRADOR)."""
    return service.crear(data, current_user)


@router.put("/{iniciativa_id}", response_model=IniciativaDetailResponse)
async def editar_iniciativa(
    iniciativa_id: int,
    data: IniciativaUpdate,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """Editar iniciativa (solo en estado BORRADOR)."""
    return service.editar(iniciativa_id, data, current_user)


# ── Acciones del flujo ─────────────────────────────────────────────────────

@router.post("/{iniciativa_id}/enviar-a-gg", response_model=IniciativaDetailResponse)
async def enviar_a_gg(
    iniciativa_id: int,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """Director envía la iniciativa a Gerencia General para aprobación."""
    return service.enviar_a_gg(iniciativa_id, current_user)


@router.post("/{iniciativa_id}/aprobar-gg", response_model=IniciativaDetailResponse)
async def aprobar_gg(
    iniciativa_id: int,
    body: IniciativaAprobarGGRequest,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """Gerencia General aprueba la iniciativa y notifica al Área 4."""
    return service.aprobar_gg(iniciativa_id, body.comment, current_user)


@router.post("/{iniciativa_id}/rechazar-gg", response_model=IniciativaDetailResponse)
async def rechazar_gg(
    iniciativa_id: int,
    body: IniciativaRechazarRequest,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """Gerencia General rechaza la iniciativa."""
    return service.rechazar_gg(iniciativa_id, body.comment, current_user)


@router.post("/{iniciativa_id}/vincular-prototipado", response_model=IniciativaDetailResponse)
async def vincular_prototipado(
    iniciativa_id: int,
    solicitud_id: int = Query(..., description="ID de la solicitud de prototipado en Área 4"),
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """Área 4 vincula su solicitud de prototipado a la iniciativa."""
    return service.vincular_solicitud_prototipado(iniciativa_id, solicitud_id, current_user)


@router.post("/{iniciativa_id}/iniciar-aprobacion-dual", response_model=IniciativaDetailResponse)
async def iniciar_aprobacion_dual(
    iniciativa_id: int,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """
    Inicia la aprobación dual (Luisa + Gerente Tiendas).
    Se llama cuando Área 4 cierra el diagnóstico técnico.
    Envía email normal a Luisa y Magic Link al Gerente de Tiendas.
    """
    return service.iniciar_aprobacion_dual(iniciativa_id, current_user)


@router.post("/{iniciativa_id}/aprobar-dual", response_model=IniciativaDetailResponse)
async def aprobar_dual_luisa(
    iniciativa_id: int,
    body: IniciativaAprobarDualRequest,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """Luisa Ibañez aprueba el prototipado (dentro de la app)."""
    return service.aprobar_dual_luisa(iniciativa_id, body.comment, current_user)


@router.post("/{iniciativa_id}/aprobar-jd", response_model=IniciativaDetailResponse)
async def aprobar_jd(
    iniciativa_id: int,
    body: IniciativaAprobarGGRequest,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """Junta Directiva aprueba. Auto-crea solicitud en INNOVACION."""
    return service.aprobar_jd(iniciativa_id, body.comment, current_user)


@router.post("/{iniciativa_id}/upload-business-case", response_model=IniciativaDetailResponse)
async def upload_business_case(
    iniciativa_id: int,
    file: UploadFile = File(...),
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
    s3: S3StorageService = Depends(get_s3_storage),
):
    """Subir o reemplazar el Business Case de una iniciativa (guardado en S3)."""
    allowed = {".pdf", ".doc", ".docx", ".pptx"}
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no permitido. Usa PDF, DOC, DOCX o PPTX.",
        )
    # Subir a S3 bajo la carpeta iniciativas/business_cases/
    content = await file.read()
    s3_key = f"iniciativas/business_cases/bc_{iniciativa_id}_{uuid.uuid4().hex[:8]}{ext}"
    s3.s3_client.put_object(
        Bucket=s3.bucket_name,
        Key=s3_key,
        Body=content,
        ContentType=file.content_type or "application/octet-stream",
        Metadata={"iniciativa_id": str(iniciativa_id), "original_filename": file.filename or ""},
    )
    updated = service.repository.update_fields(iniciativa_id, business_case_path=s3_key)
    return IniciativaDetailResponse.model_validate(updated)


@router.get("/{iniciativa_id}/download-business-case")
async def download_business_case(
    iniciativa_id: int,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
    s3: S3StorageService = Depends(get_s3_storage),
):
    """Redirige a una URL temporal firmada de S3 para descargar el Business Case."""
    iniciativa = service.repository.get_by_id(iniciativa_id)
    if not iniciativa or not iniciativa.business_case_path:
        raise HTTPException(status_code=404, detail="Business Case no encontrado")
    url = s3.get_download_url(iniciativa.business_case_path, expiration=300)
    return RedirectResponse(url=url)


@router.get("/{iniciativa_id}/magic-link")
async def obtener_magic_link(
    iniciativa_id: int,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """
    Devuelve la URL del magic link activo para el Gerente de Tiendas.
    Útil cuando el correo no llega — permite compartir el enlace manualmente.
    Solo disponible mientras la iniciativa esté en PENDIENTE_APROBACION_DUAL.
    """
    from db.models import ApprovalToken, ApprovalTokenAction, IniciativaStatus
    from core.config import settings

    iniciativa = service.repository.get_by_id(iniciativa_id)
    if not iniciativa:
        raise HTTPException(status_code=404, detail="Iniciativa no encontrada")
    if iniciativa.status != IniciativaStatus.PENDIENTE_APROBACION_DUAL:
        raise HTTPException(status_code=400, detail="La iniciativa no está en aprobación dual")

    token = (
        service.repository.db.query(ApprovalToken)
        .filter(
            ApprovalToken.iniciativa_id == iniciativa_id,
            ApprovalToken.action == ApprovalTokenAction.PENDIENTE,
        )
        .order_by(ApprovalToken.created_at.desc())
        .first()
    )
    if not token:
        raise HTTPException(status_code=404, detail="No hay token activo. Reinicia la aprobación dual.")

    from datetime import datetime
    if token.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="El token ha expirado. Reinicia la aprobación dual.")

    approve_url = f"{settings.FRONTEND_URL}/aprobar/{token.token}?action=APROBADO"
    reject_url = f"{settings.FRONTEND_URL}/aprobar/{token.token}?action=RECHAZADO"
    return {
        "approve_url": approve_url,
        "reject_url": reject_url,
        "expires_at": token.expires_at.isoformat(),
        "gerente_email": token.user_email,
    }


@router.post("/{iniciativa_id}/rechazar-jd", response_model=IniciativaDetailResponse)
async def rechazar_jd(
    iniciativa_id: int,
    body: IniciativaRechazarRequest,
    service: IniciativaService = Depends(get_service),
    current_user=Depends(get_current_user),
):
    """Junta Directiva rechaza la iniciativa."""
    return service.rechazar_jd(iniciativa_id, body.comment, current_user)
