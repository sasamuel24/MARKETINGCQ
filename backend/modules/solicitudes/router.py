"""
Router de solicitudes - Endpoints REST para gestión de solicitudes
"""
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, status, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from modules.solicitudes.schemas import (
    SolicitudCreate,
    SolicitudUpdate,
    SolicitudResponse,
    SolicitudDetailResponse,
    SolicitudListResponse,
    SolicitudAjusteRequest,
    SolicitudAprobarRequest,
    SolicitudRechazarRequest
)
from modules.solicitudes.service import SolicitudService
from modules.solicitud_files.service import SolicitudFileService
from modules.solicitud_files.schemas import SolicitudFileCreate
from core.dependencies import get_current_user_id
from core.storage import get_s3_storage, S3StorageService
from db.session import get_db


router = APIRouter(prefix="/solicitudes", tags=["Solicitudes"])


def get_solicitud_service(db: Session = Depends(get_db)) -> SolicitudService:
    """Dependency para obtener instancia de SolicitudService"""
    return SolicitudService(db)


@router.get("", response_model=SolicitudListResponse, status_code=status.HTTP_200_OK)
async def get_solicitudes(
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(10, ge=1, le=100, description="Tamaño de página"),
    area_id: Optional[int] = Query(None, description="Filtrar por área"),
    stage_id: Optional[int] = Query(None, description="Filtrar por etapa"),
    status_id: Optional[int] = Query(None, description="Filtrar por estado"),
    created_by_user_id: Optional[int] = Query(None, description="Filtrar por usuario creador"),
    check_approver: bool = Query(False, description="Si es True, filtra solicitudes donde el usuario actual es aprobador"),
    service: SolicitudService = Depends(get_solicitud_service),
    current_user_id: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener lista de solicitudes con paginación y filtros
    
    - **page**: Número de página (por defecto 1)
    - **page_size**: Tamaño de página (por defecto 10, máximo 100)
    - **area_id**: Filtrar por área específica (opcional)
    - **stage_id**: Filtrar por etapa específica (opcional)
    - **status_id**: Filtrar por estado específico (opcional)
    - **created_by_user_id**: Filtrar por usuario creador (opcional)
    - **check_approver**: Si es True, retorna solo solicitudes donde el usuario actual es aprobador de la etapa actual
    
    Las solicitudes se retornan ordenadas por fecha de creación descendente.
    Incluye información completa de área, etapa (stage), estado (state) y usuario creador.
    Requiere autenticación.
    """
    skip = (page - 1) * page_size
    
    approver_user_id = int(current_user_id) if check_approver else None
    
    solicitudes, total = service.get_all_solicitudes(
        skip=skip, 
        limit=page_size,
        area_id=area_id,
        stage_id=stage_id,
        status_id=status_id,
        created_by_user_id=created_by_user_id,
        approver_user_id=approver_user_id
    )
    
    return SolicitudListResponse(
        solicitudes=solicitudes,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/area/{area_id}", response_model=List[SolicitudDetailResponse], status_code=status.HTTP_200_OK)
async def get_solicitudes_by_area(
    area_id: int,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener todas las solicitudes de un área
    
    - **area_id**: ID del área
    
    Retorna todas las solicitudes del área ordenadas por fecha de creación descendente.
    Requiere autenticación.
    """
    return service.get_solicitudes_by_area(area_id)


@router.get("/user/{user_id}", response_model=List[SolicitudDetailResponse], status_code=status.HTTP_200_OK)
async def get_solicitudes_by_user(
    user_id: int,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener todas las solicitudes creadas por un usuario
    
    - **user_id**: ID del usuario
    
    Retorna todas las solicitudes creadas por el usuario ordenadas por fecha de creación descendente.
    Requiere autenticación.
    """
    return service.get_solicitudes_by_user(user_id)


@router.get("/{solicitud_id}", response_model=SolicitudDetailResponse, status_code=status.HTTP_200_OK)
async def get_solicitud(
    solicitud_id: int,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener una solicitud por ID
    
    - **solicitud_id**: ID de la solicitud a obtener
    
    Incluye información completa de área, etapa (stage), estado (state) y usuario creador.
    Requiere autenticación.
    """
    return service.get_solicitud_by_id(solicitud_id)


@router.post("", response_model=SolicitudDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_solicitud(
    solicitud: SolicitudCreate,
    service: SolicitudService = Depends(get_solicitud_service),
    current_user_id: str = Depends(get_current_user_id)  # Usuario autenticado
):
    """
    Crear una nueva solicitud
    
    - **title**: Título de la solicitud (requerido)
    - **description**: Descripción detallada (opcional)
    - **area_id**: ID del área (debe existir)
    - **stage_id**: ID de la etapa (debe existir y pertenecer al área)
    - **status_id**: ID del estado (debe existir)
    
    VALIDACIÓN IMPORTANTE: La etapa (stage) debe pertenecer al área especificada.
    El usuario creador se obtiene del token JWT.
    Requiere autenticación.
    """
    return service.create_solicitud(solicitud, int(current_user_id))


@router.put("/{solicitud_id}", response_model=SolicitudDetailResponse, status_code=status.HTTP_200_OK)
async def update_solicitud(
    solicitud_id: int,
    solicitud: SolicitudUpdate,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Actualizar una solicitud existente
    
    - **solicitud_id**: ID de la solicitud a actualizar
    - **title**: Nuevo título (opcional)
    - **description**: Nueva descripción (opcional)
    - **stage_id**: Nueva etapa (opcional, debe pertenecer al área de la solicitud)
    - **status_id**: Nuevo estado (opcional)
    
    Solo se actualizan los campos proporcionados.
    VALIDACIÓN IMPORTANTE: Si se cambia la etapa, debe pertenecer al área de la solicitud.
    Requiere autenticación.
    """
    return service.update_solicitud(solicitud_id, solicitud)


@router.delete("/{solicitud_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_solicitud(
    solicitud_id: int,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Eliminar una solicitud
    
    - **solicitud_id**: ID de la solicitud a eliminar
    
    Requiere autenticación.
    """
    service.delete_solicitud(solicitud_id)
    return None


@router.post("/{solicitud_id}/upload-files", status_code=status.HTTP_201_CREATED)
async def upload_files_to_solicitud(
    solicitud_id: int,
    files: List[UploadFile] = File(...),
    doc_type: str = Form("ARTE"),
    service: SolicitudService = Depends(get_solicitud_service),
    s3_service: S3StorageService = Depends(get_s3_storage),
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user_id)
):
    """
    Subir archivos a una solicitud existente
    
    - **solicitud_id**: ID de la solicitud
    - **files**: Lista de archivos a subir
    - **doc_type**: Tipo de documento (ARTE, BRIEF, EVIDENCIA)
    
    Los archivos se suben a S3 y se registran en la base de datos.
    Requiere autenticación.
    """
    # Verificar que la solicitud existe
    solicitud = service.get_solicitud_by_id(solicitud_id)
    
    uploaded_files = []
    file_service = SolicitudFileService(db)
    
    for file in files:
        # Subir archivo a S3
        file_info = await s3_service.upload_file(file, solicitud_id, doc_type)
        
        # Registrar en base de datos
        file_create = SolicitudFileCreate(
            solicitud_id=solicitud_id,
            storage_provider=file_info["storage_provider"],
            storage_path=file_info["storage_path"],
            filename=file_info["filename"],
            content_type=file_info["content_type"],
            size_bytes=file_info["size_bytes"],
            doc_type=doc_type
        )
        
        db_file = file_service.create_file(file_create)
        uploaded_files.append(db_file)
    
    return {
        "message": f"{len(uploaded_files)} archivo(s) subido(s) exitosamente",
        "files": uploaded_files
    }


@router.get("/{solicitud_id}/files/{file_id}/download", status_code=status.HTTP_200_OK)
async def get_file_download_url(
    solicitud_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    s3_service: S3StorageService = Depends(get_s3_storage),
    _: str = Depends(get_current_user_id)
):
    """
    Descargar archivo directamente
    
    - **solicitud_id**: ID de la solicitud
    - **file_id**: ID del archivo
    
    Descarga el archivo directamente desde S3 y lo envía al cliente.
    Requiere autenticación.
    """
    from fastapi.responses import StreamingResponse
    import io
    
    file_service = SolicitudFileService(db)
    file = file_service.get_file_by_id(file_id)
    
    # Verificar que el archivo pertenece a la solicitud
    if file.solicitud_id != solicitud_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en esta solicitud"
        )
    
    # Descargar archivo de S3
    file_content = s3_service.download_file(file.storage_path)
    
    # Retornar como streaming response
    return StreamingResponse(
        io.BytesIO(file_content),
        media_type=file.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{file.filename}"'
        }
    )


@router.get("/{solicitud_id}/files/{file_id}/preview", status_code=status.HTTP_200_OK)
async def get_file_preview(
    solicitud_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    s3_service: S3StorageService = Depends(get_s3_storage),
    _: str = Depends(get_current_user_id)
):
    """
    Obtener vista previa optimizada de un archivo
    
    - **solicitud_id**: ID de la solicitud
    - **file_id**: ID del archivo
    
    Para imágenes, intenta obtener el thumbnail pre-generado.
    Si no existe, genera uno on-the-fly.
    Para PDFs, retorna el archivo completo.
    Requiere autenticación.
    """
    from fastapi.responses import StreamingResponse
    import io
    from PIL import Image
    
    file_service = SolicitudFileService(db)
    file = file_service.get_file_by_id(file_id)
    
    # Verificar que el archivo pertenece a la solicitud
    if file.solicitud_id != solicitud_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado en esta solicitud"
        )
    
    # Si es imagen, intentar obtener thumbnail pre-generado
    if file.content_type.startswith('image/'):
        # Intentar obtener thumbnail primero
        thumbnail_content = s3_service.download_thumbnail(file.storage_path)
        
        if thumbnail_content:
            # Retornar thumbnail pre-generado (más rápido)
            return StreamingResponse(
                io.BytesIO(thumbnail_content),
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        
        # Si no hay thumbnail, generar on-the-fly (fallback)
        try:
            file_content = s3_service.download_file(file.storage_path)
            
            # Abrir imagen con mejor manejo de formatos
            img = Image.open(io.BytesIO(file_content))
            img.load()
            
            # Manejar diferentes modos de color
            if img.mode in ('RGBA', 'LA', 'PA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'PA':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                img = background
            elif img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            if img.mode == 'L':
                img = img.convert('RGB')
            
            # Calcular nuevo tamaño
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            # Guardar como JPEG optimizado
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            output.seek(0)
            
            return StreamingResponse(
                output,
                media_type="image/jpeg",
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        except Exception as e:
            # Si falla todo, retornar imagen original
            import traceback
            print(f"Error generating thumbnail for file {file.filename}: {e}")
            print(traceback.format_exc())
            file_content = s3_service.download_file(file.storage_path)
            return StreamingResponse(
                io.BytesIO(file_content),
                media_type=file.content_type,
                headers={
                    "Cache-Control": "public, max-age=86400",
                    "Access-Control-Allow-Origin": "*"
                }
            )
    else:
        # Para PDFs y otros, retornar archivo completo
        file_content = s3_service.download_file(file.storage_path)
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=file.content_type,
            headers={
                "Cache-Control": "public, max-age=86400",
                "Access-Control-Allow-Origin": "*"
            }
        )



@router.post("/{solicitud_id}/solicitar-ajustes", response_model=SolicitudDetailResponse, status_code=status.HTTP_200_OK)
async def solicitar_ajustes(
    solicitud_id: int,
    ajuste_request: SolicitudAjusteRequest,
    service: SolicitudService = Depends(get_solicitud_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Solicitar ajustes en una solicitud
    
    - **solicitud_id**: ID de la solicitud
    - **comment**: Comentario explicando los ajustes necesarios
    
    Cambia el estado de la solicitud a "AJUSTES_SOLICITADOS" y registra el evento.
    El CREATOR podrá ver los comentarios y subir una nueva versión.
    Requiere autenticación.
    """
    return service.solicitar_ajustes(
        solicitud_id=solicitud_id,
        comment=ajuste_request.comment,
        actor_user_id=int(current_user_id)
    )


@router.get("/{solicitud_id}/eventos", status_code=status.HTTP_200_OK)
async def get_solicitud_eventos(
    solicitud_id: int,
    service: SolicitudService = Depends(get_solicitud_service),
    _: str = Depends(get_current_user_id)
):
    """
    Obtener historial de eventos de una solicitud
    
    - **solicitud_id**: ID de la solicitud
    
    Retorna todos los eventos/comentarios de la solicitud ordenados cronológicamente.
    Requiere autenticación.
    """
    return service.get_eventos_by_solicitud(solicitud_id)


@router.post("/{solicitud_id}/aprobar", response_model=SolicitudDetailResponse, status_code=status.HTTP_200_OK)
async def aprobar_solicitud(
    solicitud_id: int,
    aprobar_request: SolicitudAprobarRequest,
    service: SolicitudService = Depends(get_solicitud_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Aprobar una solicitud y avanzar a la siguiente etapa
    
    - **solicitud_id**: ID de la solicitud
    - **comment**: Comentario opcional al aprobar
    
    Si hay una siguiente etapa, la solicitud avanza automáticamente.
    Si es la última etapa, la solicitud se marca como APROBADO_FINAL.
    Requiere autenticación y que el usuario sea aprobador de la etapa actual.
    """
    return service.aprobar_solicitud(
        solicitud_id=solicitud_id,
        comment=aprobar_request.comment,
        actor_user_id=int(current_user_id)
    )


@router.post("/{solicitud_id}/rechazar", response_model=SolicitudDetailResponse, status_code=status.HTTP_200_OK)
async def rechazar_solicitud(
    solicitud_id: int,
    rechazar_request: SolicitudRechazarRequest,
    service: SolicitudService = Depends(get_solicitud_service),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Rechazar una solicitud
    
    - **solicitud_id**: ID de la solicitud
    - **comment**: Comentario explicando el motivo del rechazo (requerido)
    
    La solicitud se marca como RECHAZADO.
    Requiere autenticación y que el usuario sea aprobador de la etapa actual.
    """
    return service.rechazar_solicitud(
        solicitud_id=solicitud_id,
        comment=rechazar_request.comment,
        actor_user_id=int(current_user_id)
    )

