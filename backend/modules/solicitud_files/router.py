"""
Router de solicitud_files - Endpoints REST para gestión de archivos de solicitudes
"""
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from modules.solicitud_files.schemas import (
    SolicitudFileCreate,
    SolicitudFileUpdate,
    SolicitudFileResponse,
    SolicitudFileDetailResponse,
    SolicitudFileListResponse
)
from modules.solicitud_files.service import SolicitudFileService
from core.dependencies import get_current_user_id
from core.storage import get_s3_storage, S3StorageService
from db.session import get_db


router = APIRouter(prefix="/solicitud-files", tags=["Solicitud Files"])


def get_solicitud_file_service(db: Session = Depends(get_db)) -> SolicitudFileService:
    """Dependency para obtener instancia de SolicitudFileService"""
    return SolicitudFileService(db)


@router.get("", response_model=SolicitudFileListResponse, status_code=status.HTTP_200_OK)
async def get_solicitud_files(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros"),
    solicitud_id: Optional[int] = Query(None, description="Filtrar por solicitud"),
    doc_type: Optional[str] = Query(None, description="Filtrar por tipo de documento"),
    service: SolicitudFileService = Depends(get_solicitud_file_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener lista de archivos con paginación y filtros
    
    - **skip**: Número de registros a saltar (por defecto 0)
    - **limit**: Límite de registros (por defecto 100, máximo 100)
    - **solicitud_id**: Filtrar por solicitud específica (opcional)
    - **doc_type**: Filtrar por tipo de documento (opcional)
    
    Los archivos se retornan ordenados por fecha de creación descendente.
    Incluye información de la solicitud relacionada.
    Requiere autenticación.
    """
    files, total = service.get_all_files(
        skip=skip, 
        limit=limit,
        solicitud_id=solicitud_id,
        doc_type=doc_type
    )
    
    return SolicitudFileListResponse(
        items=files,
        total=total
    )


@router.get("/solicitud/{solicitud_id}", response_model=List[SolicitudFileDetailResponse], status_code=status.HTTP_200_OK)
async def get_files_by_solicitud(
    solicitud_id: int,
    service: SolicitudFileService = Depends(get_solicitud_file_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener todos los archivos de una solicitud
    
    - **solicitud_id**: ID de la solicitud
    
    Retorna todos los archivos de la solicitud ordenados por fecha de creación descendente.
    Requiere autenticación.
    """
    return service.get_files_by_solicitud(solicitud_id)


@router.get("/solicitud/{solicitud_id}/doc-type/{doc_type}", response_model=List[SolicitudFileDetailResponse], status_code=status.HTTP_200_OK)
async def get_files_by_solicitud_and_doc_type(
    solicitud_id: int,
    doc_type: str,
    service: SolicitudFileService = Depends(get_solicitud_file_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener archivos de una solicitud filtrados por tipo de documento
    
    - **solicitud_id**: ID de la solicitud
    - **doc_type**: Tipo de documento (ARTE, BRIEF, EVIDENCIA, etc.)
    
    Útil para obtener todos los archivos de un tipo específico de una solicitud.
    Requiere autenticación.
    """
    return service.get_files_by_solicitud_and_doc_type(solicitud_id, doc_type)


@router.get("/solicitud/{solicitud_id}/total-size", status_code=status.HTTP_200_OK)
async def get_total_size_by_solicitud(
    solicitud_id: int,
    service: SolicitudFileService = Depends(get_solicitud_file_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener el tamaño total de archivos de una solicitud
    
    - **solicitud_id**: ID de la solicitud
    
    Retorna información sobre el tamaño total en bytes y MB, y el número de archivos.
    Útil para validar límites de almacenamiento.
    Requiere autenticación.
    """
    return service.get_total_size_by_solicitud(solicitud_id)


@router.get("/{file_id}", response_model=SolicitudFileDetailResponse, status_code=status.HTTP_200_OK)
async def get_solicitud_file(
    file_id: int,
    service: SolicitudFileService = Depends(get_solicitud_file_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Obtener un archivo por ID
    
    - **file_id**: ID del archivo a obtener
    
    Incluye información completa de la solicitud relacionada.
    Requiere autenticación.
    """
    return service.get_file_by_id(file_id)


@router.post("", response_model=SolicitudFileDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_solicitud_file(
    file: SolicitudFileCreate,
    service: SolicitudFileService = Depends(get_solicitud_file_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Crear un nuevo registro de archivo
    
    - **solicitud_id**: ID de la solicitud (debe existir)
    - **storage_provider**: Proveedor de almacenamiento (s3, local, gcs)
    - **storage_path**: Ruta completa del archivo en el storage
    - **filename**: Nombre original del archivo
    - **content_type**: Tipo MIME (image/png, application/pdf, etc.)
    - **size_bytes**: Tamaño en bytes (debe ser >= 0)
    - **doc_type**: Tipo de documento (ARTE, BRIEF, EVIDENCIA, etc.)
    
    VALIDACIÓN: No puede existir otro archivo con la misma storage_path en la misma solicitud.
    Requiere autenticación.
    """
    return service.create_file(file)


@router.put("/{file_id}", response_model=SolicitudFileDetailResponse, status_code=status.HTTP_200_OK)
async def update_solicitud_file(
    file_id: int,
    file: SolicitudFileUpdate,
    service: SolicitudFileService = Depends(get_solicitud_file_service),
    _: str = Depends(get_current_user_id)  # Requiere autenticación
):
    """
    Actualizar un archivo existente
    
    - **file_id**: ID del archivo a actualizar
    - **filename**: Nuevo nombre del archivo (opcional)
    - **doc_type**: Nuevo tipo de documento (opcional)
    
    Solo se actualizan los campos proporcionados.
    Nota: No se permite cambiar storage_path, storage_provider, etc.
    Requiere autenticación.
    """
    return service.update_file(file_id, file)


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_solicitud_file(
    file_id: int,
    service: SolicitudFileService = Depends(get_solicitud_file_service),
    s3_service: S3StorageService = Depends(get_s3_storage),
    _: str = Depends(get_current_user_id)
):
    """
    Eliminar un archivo de la BD y de S3.

    - **file_id**: ID del archivo a eliminar

    Requiere autenticación.
    """
    # Obtener el archivo antes de borrarlo para conocer el storage_path
    file = service.get_file_by_id(file_id)

    # Intentar eliminar de S3 (no falla si el objeto ya no existe)
    try:
        s3_service.delete_file(file.storage_path)
    except Exception:
        pass

    service.delete_file(file_id)
    return None
