"""
Repositorio para operaciones con solicitud_files en la base de datos
"""
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from db.models import SolicitudFile
from modules.solicitud_files.schemas import SolicitudFileCreate, SolicitudFileUpdate


class SolicitudFileRepository:
    """Repositorio para gestionar operaciones CRUD de solicitud_files"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, file_id: int, include_relations: bool = False) -> Optional[SolicitudFile]:
        """
        Obtener archivo por ID
        
        Args:
            file_id: ID del archivo
            include_relations: Si True, incluye solicitud
            
        Returns:
            SolicitudFile encontrado o None
        """
        query = self.db.query(SolicitudFile)
        if include_relations:
            query = query.options(joinedload(SolicitudFile.solicitud))
        return query.filter(SolicitudFile.id == file_id).first()
    
    def get_by_storage_path(self, solicitud_id: int, storage_path: str) -> Optional[SolicitudFile]:
        """
        Obtener archivo por solicitud y storage_path
        
        Args:
            solicitud_id: ID de la solicitud
            storage_path: Ruta del archivo en el storage
            
        Returns:
            SolicitudFile encontrado o None
        """
        return self.db.query(SolicitudFile).filter(
            SolicitudFile.solicitud_id == solicitud_id,
            SolicitudFile.storage_path == storage_path
        ).first()
    
    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        solicitud_id: Optional[int] = None,
        doc_type: Optional[str] = None,
        include_relations: bool = True
    ) -> List[SolicitudFile]:
        """
        Obtener todos los archivos con paginación y filtros
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            solicitud_id: Filtrar por solicitud (opcional)
            doc_type: Filtrar por tipo de documento (opcional)
            include_relations: Si True, incluye solicitud
            
        Returns:
            Lista de archivos ordenados por created_at desc
        """
        query = self.db.query(SolicitudFile)
        if include_relations:
            query = query.options(joinedload(SolicitudFile.solicitud))
        if solicitud_id:
            query = query.filter(SolicitudFile.solicitud_id == solicitud_id)
        if doc_type:
            query = query.filter(SolicitudFile.doc_type == doc_type)
        
        return query.order_by(SolicitudFile.created_at.desc()).offset(skip).limit(limit).all()
    
    def count(
        self,
        solicitud_id: Optional[int] = None,
        doc_type: Optional[str] = None
    ) -> int:
        """
        Contar archivos con filtros
        
        Args:
            solicitud_id: Filtrar por solicitud (opcional)
            doc_type: Filtrar por tipo de documento (opcional)
            
        Returns:
            Número de archivos
        """
        query = self.db.query(SolicitudFile)
        if solicitud_id:
            query = query.filter(SolicitudFile.solicitud_id == solicitud_id)
        if doc_type:
            query = query.filter(SolicitudFile.doc_type == doc_type)
        
        return query.count()
    
    def create(self, file_data: SolicitudFileCreate) -> SolicitudFile:
        """
        Crear un nuevo archivo
        
        Args:
            file_data: Datos del archivo
            
        Returns:
            SolicitudFile creado
            
        Raises:
            IntegrityError: Si hay un error de integridad (duplicado, FK inválida, etc.)
        """
        db_file = SolicitudFile(
            solicitud_id=file_data.solicitud_id,
            storage_provider=file_data.storage_provider,
            storage_path=file_data.storage_path,
            filename=file_data.filename,
            content_type=file_data.content_type,
            size_bytes=file_data.size_bytes,
            doc_type=file_data.doc_type
        )
        self.db.add(db_file)
        self.db.commit()
        self.db.refresh(db_file)
        
        # Recargar con relaciones
        return self.get_by_id(db_file.id, include_relations=True)
    
    def update(self, file_id: int, file_data: SolicitudFileUpdate) -> Optional[SolicitudFile]:
        """
        Actualizar un archivo existente
        
        Args:
            file_id: ID del archivo a actualizar
            file_data: Datos a actualizar
            
        Returns:
            SolicitudFile actualizado o None si no existe
            
        Raises:
            IntegrityError: Si hay un error de integridad
        """
        db_file = self.get_by_id(file_id)
        if not db_file:
            return None
        
        # Actualizar solo los campos proporcionados
        update_data = file_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_file, field, value)
        
        self.db.commit()
        self.db.refresh(db_file)
        
        # Recargar con relaciones
        return self.get_by_id(db_file.id, include_relations=True)
    
    def delete(self, file_id: int) -> bool:
        """
        Eliminar un archivo
        
        Args:
            file_id: ID del archivo a eliminar
            
        Returns:
            True si se eliminó, False si no existía
        """
        db_file = self.get_by_id(file_id)
        if not db_file:
            return False
        
        self.db.delete(db_file)
        self.db.commit()
        return True
    
    def get_by_solicitud(self, solicitud_id: int, include_relations: bool = True) -> List[SolicitudFile]:
        """
        Obtener todos los archivos de una solicitud
        
        Args:
            solicitud_id: ID de la solicitud
            include_relations: Si True, incluye solicitud
            
        Returns:
            Lista de archivos de la solicitud
        """
        query = self.db.query(SolicitudFile).filter(SolicitudFile.solicitud_id == solicitud_id)
        if include_relations:
            query = query.options(joinedload(SolicitudFile.solicitud))
        return query.order_by(SolicitudFile.created_at.desc()).all()
    
    def get_by_solicitud_and_doc_type(
        self, 
        solicitud_id: int, 
        doc_type: str,
        include_relations: bool = True
    ) -> List[SolicitudFile]:
        """
        Obtener archivos de una solicitud filtrados por tipo de documento
        
        Args:
            solicitud_id: ID de la solicitud
            doc_type: Tipo de documento
            include_relations: Si True, incluye solicitud
            
        Returns:
            Lista de archivos del tipo especificado
        """
        query = self.db.query(SolicitudFile).filter(
            SolicitudFile.solicitud_id == solicitud_id,
            SolicitudFile.doc_type == doc_type
        )
        if include_relations:
            query = query.options(joinedload(SolicitudFile.solicitud))
        return query.order_by(SolicitudFile.created_at.desc()).all()
    
    def get_total_size_by_solicitud(self, solicitud_id: int) -> int:
        """
        Obtener el tamaño total en bytes de todos los archivos de una solicitud
        
        Args:
            solicitud_id: ID de la solicitud
            
        Returns:
            Tamaño total en bytes
        """
        result = self.db.query(
            self.db.func.sum(SolicitudFile.size_bytes)
        ).filter(
            SolicitudFile.solicitud_id == solicitud_id
        ).scalar()
        
        return result or 0
