"""
Servicio de solicitud_files - Lógica de negocio
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from modules.solicitud_files.repository import SolicitudFileRepository
from modules.solicitud_files.schemas import SolicitudFileCreate, SolicitudFileUpdate, SolicitudFileResponse, SolicitudFileDetailResponse
from modules.solicitudes.repository import SolicitudRepository


class SolicitudFileService:
    """Servicio para gestionar la lógica de negocio de solicitud_files"""
    
    def __init__(self, db: Session):
        self.repository = SolicitudFileRepository(db)
        self.solicitud_repository = SolicitudRepository(db)
    
    def get_file_by_id(self, file_id: int) -> SolicitudFileDetailResponse:
        """
        Obtener archivo por ID con información completa
        
        Args:
            file_id: ID del archivo
            
        Returns:
            Archivo encontrado
            
        Raises:
            HTTPException: Si el archivo no existe
        """
        file = self.repository.get_by_id(file_id, include_relations=True)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archivo con ID {file_id} no encontrado"
            )
        return SolicitudFileDetailResponse.model_validate(file)
    
    def get_all_files(
        self, 
        skip: int = 0, 
        limit: int = 100,
        solicitud_id: Optional[int] = None,
        doc_type: Optional[str] = None
    ) -> tuple[List[SolicitudFileDetailResponse], int]:
        """
        Obtener todos los archivos con paginación y filtros
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            solicitud_id: Filtrar por solicitud (opcional)
            doc_type: Filtrar por tipo de documento (opcional)
            
        Returns:
            Tupla con (lista de archivos, total de archivos)
        """
        files = self.repository.get_all(
            skip=skip, 
            limit=limit,
            solicitud_id=solicitud_id,
            doc_type=doc_type,
            include_relations=True
        )
        total = self.repository.count(solicitud_id=solicitud_id, doc_type=doc_type)
        return [SolicitudFileDetailResponse.model_validate(f) for f in files], total
    
    def create_file(self, file_data: SolicitudFileCreate) -> SolicitudFileDetailResponse:
        """
        Crear un nuevo archivo
        
        Args:
            file_data: Datos del archivo a crear
            
        Returns:
            Archivo creado
            
        Raises:
            HTTPException: Si la solicitud no existe o si el archivo ya existe
        """
        # Verificar que la solicitud existe
        if not self.solicitud_repository.get_by_id(file_data.solicitud_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La solicitud con ID {file_data.solicitud_id} no existe"
            )
        
        # Verificar si ya existe un archivo con la misma ruta en la solicitud
        existing = self.repository.get_by_storage_path(file_data.solicitud_id, file_data.storage_path)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un archivo con la ruta '{file_data.storage_path}' en la solicitud {file_data.solicitud_id}"
            )
        
        # Validar tamaño de archivo
        if file_data.size_bytes < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El tamaño del archivo debe ser mayor o igual a 0"
            )
        
        try:
            file = self.repository.create(file_data)
            return SolicitudFileDetailResponse.model_validate(file)
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error de integridad al crear el archivo: {str(e)}"
            )
    
    def update_file(self, file_id: int, file_data: SolicitudFileUpdate) -> SolicitudFileDetailResponse:
        """
        Actualizar un archivo existente
        
        Args:
            file_id: ID del archivo a actualizar
            file_data: Datos a actualizar
            
        Returns:
            Archivo actualizado
            
        Raises:
            HTTPException: Si el archivo no existe
        """
        # Verificar que el archivo existe
        if not self.repository.get_by_id(file_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archivo con ID {file_id} no encontrado"
            )
        
        try:
            file = self.repository.update(file_id, file_data)
            if not file:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Archivo con ID {file_id} no encontrado"
                )
            return SolicitudFileDetailResponse.model_validate(file)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error de integridad al actualizar el archivo."
            )
    
    def delete_file(self, file_id: int) -> None:
        """
        Eliminar un archivo
        
        Args:
            file_id: ID del archivo a eliminar
            
        Raises:
            HTTPException: Si el archivo no existe
        """
        if not self.repository.delete(file_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archivo con ID {file_id} no encontrado"
            )
    
    def get_files_by_solicitud(self, solicitud_id: int) -> List[SolicitudFileDetailResponse]:
        """
        Obtener todos los archivos de una solicitud
        
        Args:
            solicitud_id: ID de la solicitud
            
        Returns:
            Lista de archivos de la solicitud
            
        Raises:
            HTTPException: Si la solicitud no existe
        """
        # Verificar que la solicitud existe
        if not self.solicitud_repository.get_by_id(solicitud_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La solicitud con ID {solicitud_id} no existe"
            )
        
        files = self.repository.get_by_solicitud(solicitud_id, include_relations=True)
        return [SolicitudFileDetailResponse.model_validate(f) for f in files]
    
    def get_files_by_solicitud_and_doc_type(
        self, 
        solicitud_id: int, 
        doc_type: str
    ) -> List[SolicitudFileDetailResponse]:
        """
        Obtener archivos de una solicitud filtrados por tipo de documento
        
        Args:
            solicitud_id: ID de la solicitud
            doc_type: Tipo de documento
            
        Returns:
            Lista de archivos del tipo especificado
            
        Raises:
            HTTPException: Si la solicitud no existe
        """
        # Verificar que la solicitud existe
        if not self.solicitud_repository.get_by_id(solicitud_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La solicitud con ID {solicitud_id} no existe"
            )
        
        files = self.repository.get_by_solicitud_and_doc_type(
            solicitud_id, 
            doc_type,
            include_relations=True
        )
        return [SolicitudFileDetailResponse.model_validate(f) for f in files]
    
    def get_total_size_by_solicitud(self, solicitud_id: int) -> dict:
        """
        Obtener el tamaño total de archivos de una solicitud
        
        Args:
            solicitud_id: ID de la solicitud
            
        Returns:
            Diccionario con información del tamaño total
            
        Raises:
            HTTPException: Si la solicitud no existe
        """
        # Verificar que la solicitud existe
        if not self.solicitud_repository.get_by_id(solicitud_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La solicitud con ID {solicitud_id} no existe"
            )
        
        total_bytes = self.repository.get_total_size_by_solicitud(solicitud_id)
        total_mb = round(total_bytes / (1024 * 1024), 2)
        file_count = self.repository.count(solicitud_id=solicitud_id)
        
        return {
            "solicitud_id": solicitud_id,
            "total_bytes": total_bytes,
            "total_mb": total_mb,
            "file_count": file_count
        }
