"""
Servicio de solicitudes - Lógica de negocio
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from modules.solicitudes.repository import SolicitudRepository
from modules.solicitudes.schemas import SolicitudCreate, SolicitudUpdate, SolicitudResponse, SolicitudDetailResponse
from modules.areas.repository import AreaRepository
from modules.etapas.repository import EtapaRepository
from modules.estados.repository import EstadoRepository
from modules.usuarios.repository import UserRepository


class SolicitudService:
    """Servicio para gestionar la lógica de negocio de solicitudes"""
    
    def __init__(self, db: Session):
        self.repository = SolicitudRepository(db)
        self.area_repository = AreaRepository(db)
        self.etapa_repository = EtapaRepository(db)
        self.estado_repository = EstadoRepository(db)
        self.user_repository = UserRepository(db)
    
    def get_solicitud_by_id(self, solicitud_id: int) -> SolicitudDetailResponse:
        """
        Obtener solicitud por ID con información completa
        
        Args:
            solicitud_id: ID de la solicitud
            
        Returns:
            Solicitud encontrada
            
        Raises:
            HTTPException: Si la solicitud no existe
        """
        solicitud = self.repository.get_by_id(solicitud_id, include_relations=True)
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud con ID {solicitud_id} no encontrada"
            )
        return SolicitudDetailResponse.model_validate(solicitud)
    
    def get_all_solicitudes(
        self, 
        skip: int = 0, 
        limit: int = 100,
        area_id: Optional[int] = None,
        stage_id: Optional[int] = None,
        status_id: Optional[int] = None,
        created_by_user_id: Optional[int] = None,
        approver_user_id: Optional[int] = None
    ) -> tuple[List[SolicitudDetailResponse], int]:
        """
        Obtener todas las solicitudes con paginación y filtros
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            area_id: Filtrar por área (opcional)
            stage_id: Filtrar por etapa (opcional)
            status_id: Filtrar por estado (opcional)
            created_by_user_id: Filtrar por usuario creador (opcional)
            approver_user_id: Filtrar por usuario aprobador (opcional)
            
        Returns:
            Tupla con (lista de solicitudes, total de solicitudes)
        """
        solicitudes = self.repository.get_all(
            skip=skip, 
            limit=limit,
            area_id=area_id,
            stage_id=stage_id,
            status_id=status_id,
            created_by_user_id=created_by_user_id,
            approver_user_id=approver_user_id,
            include_relations=True
        )
        total = self.repository.count(
            area_id=area_id,
            stage_id=stage_id,
            status_id=status_id,
            created_by_user_id=created_by_user_id,
            approver_user_id=approver_user_id
        )
        return [SolicitudDetailResponse.model_validate(s) for s in solicitudes], total
    
    def create_solicitud(self, solicitud_data: SolicitudCreate, created_by_user_id: int) -> SolicitudDetailResponse:
        """
        Crear una nueva solicitud
        
        Args:
            solicitud_data: Datos de la solicitud a crear
            created_by_user_id: ID del usuario que crea la solicitud
            
        Returns:
            Solicitud creada
            
        Raises:
            HTTPException: Si área, etapa, estado o usuario no existen, o si hay inconsistencias
        """
        # Verificar que el área existe
        area = self.area_repository.get_by_id(solicitud_data.area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El área con ID {solicitud_data.area_id} no existe"
            )
        
        # Verificar que la etapa existe
        etapa = self.etapa_repository.get_by_id(solicitud_data.stage_id)
        if not etapa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La etapa con ID {solicitud_data.stage_id} no existe"
            )
        
        # VALIDACIÓN DE NEGOCIO: Verificar que la etapa pertenezca al área
        if etapa.area_id != solicitud_data.area_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La etapa {solicitud_data.stage_id} no pertenece al área {solicitud_data.area_id}. La etapa pertenece al área {etapa.area_id}"
            )
        
        # Verificar que el estado existe
        if not self.estado_repository.get_by_id(solicitud_data.status_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El estado con ID {solicitud_data.status_id} no existe"
            )
        
        # Verificar que el usuario creador existe
        if not self.user_repository.get_by_id(created_by_user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El usuario con ID {created_by_user_id} no existe"
            )
        
        try:
            solicitud = self.repository.create(solicitud_data, created_by_user_id)
            return SolicitudDetailResponse.model_validate(solicitud)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error de integridad al crear la solicitud. Verifique que todas las referencias sean válidas."
            )
    
    def update_solicitud(self, solicitud_id: int, solicitud_data: SolicitudUpdate) -> SolicitudDetailResponse:
        """
        Actualizar una solicitud existente
        
        Args:
            solicitud_id: ID de la solicitud a actualizar
            solicitud_data: Datos a actualizar
            
        Returns:
            Solicitud actualizada
            
        Raises:
            HTTPException: Si la solicitud no existe o hay inconsistencias
        """
        # Verificar que la solicitud existe
        solicitud = self.repository.get_by_id(solicitud_id)
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud con ID {solicitud_id} no encontrada"
            )
        
        # Si se actualiza el stage_id, validar que pertenezca al área
        if solicitud_data.stage_id is not None:
            etapa = self.etapa_repository.get_by_id(solicitud_data.stage_id)
            if not etapa:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La etapa con ID {solicitud_data.stage_id} no existe"
                )
            
            # VALIDACIÓN DE NEGOCIO: Verificar que la etapa pertenezca al área de la solicitud
            if etapa.area_id != solicitud.area_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"La etapa {solicitud_data.stage_id} no pertenece al área {solicitud.area_id} de la solicitud"
                )
        
        # Si se actualiza el status_id, verificar que existe
        if solicitud_data.status_id is not None:
            if not self.estado_repository.get_by_id(solicitud_data.status_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El estado con ID {solicitud_data.status_id} no existe"
                )
        
        try:
            solicitud = self.repository.update(solicitud_id, solicitud_data)
            if not solicitud:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Solicitud con ID {solicitud_id} no encontrada"
                )
            return SolicitudDetailResponse.model_validate(solicitud)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error de integridad al actualizar la solicitud."
            )
    
    def delete_solicitud(self, solicitud_id: int) -> None:
        """
        Eliminar una solicitud
        
        Args:
            solicitud_id: ID de la solicitud a eliminar
            
        Raises:
            HTTPException: Si la solicitud no existe
        """
        if not self.repository.delete(solicitud_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud con ID {solicitud_id} no encontrada"
            )
    
    def get_solicitudes_by_area(self, area_id: int) -> List[SolicitudDetailResponse]:
        """
        Obtener todas las solicitudes de un área
        
        Args:
            area_id: ID del área
            
        Returns:
            Lista de solicitudes del área
            
        Raises:
            HTTPException: Si el área no existe
        """
        # Verificar que el área existe
        if not self.area_repository.get_by_id(area_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El área con ID {area_id} no existe"
            )
        
        solicitudes = self.repository.get_by_area(area_id, include_relations=True)
        return [SolicitudDetailResponse.model_validate(s) for s in solicitudes]
    
    def get_solicitudes_by_user(self, user_id: int) -> List[SolicitudDetailResponse]:
        """
        Obtener todas las solicitudes creadas por un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Lista de solicitudes del usuario
            
        Raises:
            HTTPException: Si el usuario no existe
        """
        # Verificar que el usuario existe
        if not self.user_repository.get_by_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El usuario con ID {user_id} no existe"
            )
        
        solicitudes = self.repository.get_by_user(user_id, include_relations=True)
        return [SolicitudDetailResponse.model_validate(s) for s in solicitudes]
