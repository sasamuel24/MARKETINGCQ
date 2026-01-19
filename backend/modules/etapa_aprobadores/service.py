"""
Servicio de etapa_aprobadores - Lógica de negocio
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from modules.etapa_aprobadores.repository import EtapaAprobadorRepository
from modules.etapa_aprobadores.schemas import EtapaAprobadorCreate, EtapaAprobadorUpdate, EtapaAprobadorResponse, EtapaAprobadorDetailResponse
from modules.etapas.repository import EtapaRepository
from modules.usuarios.repository import UserRepository


class EtapaAprobadorService:
    """Servicio para gestionar la lógica de negocio de etapa_aprobadores"""
    
    def __init__(self, db: Session):
        self.repository = EtapaAprobadorRepository(db)
        self.etapa_repository = EtapaRepository(db)
        self.usuario_repository = UserRepository(db)
    
    def get_etapa_aprobador_by_id(self, etapa_aprobador_id: int) -> EtapaAprobadorDetailResponse:
        """
        Obtener etapa aprobador por ID con información de la etapa y usuario
        
        Args:
            etapa_aprobador_id: ID del etapa aprobador
            
        Returns:
            EtapaAprobador encontrado
            
        Raises:
            HTTPException: Si el etapa aprobador no existe
        """
        etapa_aprobador = self.repository.get_by_id(etapa_aprobador_id, include_relations=True)
        if not etapa_aprobador:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asignación con ID {etapa_aprobador_id} no encontrada"
            )
        return EtapaAprobadorDetailResponse.model_validate(etapa_aprobador)
    
    def get_all_etapa_aprobadores(
        self, 
        skip: int = 0, 
        limit: int = 100,
        etapa_id: Optional[int] = None,
        user_id: Optional[int] = None,
        only_active: bool = False
    ) -> tuple[List[EtapaAprobadorDetailResponse], int]:
        """
        Obtener todos los etapa aprobadores con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            etapa_id: Filtrar por etapa (opcional)
            user_id: Filtrar por usuario (opcional)
            only_active: Si True, solo retorna asignaciones activas
            
        Returns:
            Tupla con (lista de etapa aprobadores, total de etapa aprobadores)
        """
        etapa_aprobadores = self.repository.get_all(
            skip=skip, 
            limit=limit, 
            etapa_id=etapa_id,
            user_id=user_id,
            only_active=only_active,
            include_relations=True
        )
        total = self.repository.count(etapa_id=etapa_id, user_id=user_id, only_active=only_active)
        return [EtapaAprobadorDetailResponse.model_validate(ea) for ea in etapa_aprobadores], total
    
    def create_etapa_aprobador(self, etapa_aprobador_data: EtapaAprobadorCreate) -> EtapaAprobadorDetailResponse:
        """
        Crear un nuevo etapa aprobador
        
        Args:
            etapa_aprobador_data: Datos del etapa aprobador a crear
            
        Returns:
            EtapaAprobador creado
            
        Raises:
            HTTPException: Si la etapa o usuario no existen o si la asignación ya existe
        """
        # Verificar que la etapa existe
        if not self.etapa_repository.get_by_id(etapa_aprobador_data.etapa_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La etapa con ID {etapa_aprobador_data.etapa_id} no existe"
            )
        
        # Verificar que el usuario existe
        if not self.usuario_repository.get_by_id(etapa_aprobador_data.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El usuario con ID {etapa_aprobador_data.user_id} no existe"
            )
        
        # Verificar si la asignación ya existe
        existing = self.repository.get_by_etapa_and_user(
            etapa_aprobador_data.etapa_id, 
            etapa_aprobador_data.user_id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una asignación para la etapa {etapa_aprobador_data.etapa_id} y usuario {etapa_aprobador_data.user_id}"
            )
        
        try:
            etapa_aprobador = self.repository.create(etapa_aprobador_data)
            return EtapaAprobadorDetailResponse.model_validate(etapa_aprobador)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error de integridad al crear la asignación. Verifique que la etapa y usuario sean válidos."
            )
    
    def update_etapa_aprobador(self, etapa_aprobador_id: int, etapa_aprobador_data: EtapaAprobadorUpdate) -> EtapaAprobadorDetailResponse:
        """
        Actualizar un etapa aprobador existente
        
        Args:
            etapa_aprobador_id: ID del etapa aprobador a actualizar
            etapa_aprobador_data: Datos a actualizar
            
        Returns:
            EtapaAprobador actualizado
            
        Raises:
            HTTPException: Si el etapa aprobador no existe
        """
        # Verificar que existe
        if not self.repository.get_by_id(etapa_aprobador_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asignación con ID {etapa_aprobador_id} no encontrada"
            )
        
        try:
            etapa_aprobador = self.repository.update(etapa_aprobador_id, etapa_aprobador_data)
            if not etapa_aprobador:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Asignación con ID {etapa_aprobador_id} no encontrada"
                )
            return EtapaAprobadorDetailResponse.model_validate(etapa_aprobador)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Error de integridad al actualizar la asignación."
            )
    
    def delete_etapa_aprobador(self, etapa_aprobador_id: int) -> None:
        """
        Eliminar un etapa aprobador
        
        Args:
            etapa_aprobador_id: ID del etapa aprobador a eliminar
            
        Raises:
            HTTPException: Si el etapa aprobador no existe
        """
        if not self.repository.delete(etapa_aprobador_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Asignación con ID {etapa_aprobador_id} no encontrada"
            )
    
    def get_aprobadores_by_etapa(self, etapa_id: int, only_active: bool = True) -> List[EtapaAprobadorDetailResponse]:
        """
        Obtener todos los aprobadores de una etapa
        
        Args:
            etapa_id: ID de la etapa
            only_active: Si True, solo retorna aprobadores activos
            
        Returns:
            Lista de aprobadores de la etapa
            
        Raises:
            HTTPException: Si la etapa no existe
        """
        # Verificar que la etapa existe
        if not self.etapa_repository.get_by_id(etapa_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La etapa con ID {etapa_id} no existe"
            )
        
        aprobadores = self.repository.get_aprobadores_by_etapa(etapa_id, only_active=only_active)
        return [EtapaAprobadorDetailResponse.model_validate(ea) for ea in aprobadores]
    
    def get_etapas_by_usuario(self, user_id: int, only_active: bool = True) -> List[EtapaAprobadorDetailResponse]:
        """
        Obtener todas las etapas donde el usuario es aprobador
        
        Args:
            user_id: ID del usuario
            only_active: Si True, solo retorna asignaciones activas
            
        Returns:
            Lista de etapas donde el usuario es aprobador
            
        Raises:
            HTTPException: Si el usuario no existe
        """
        # Verificar que el usuario existe
        if not self.usuario_repository.get_by_id(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El usuario con ID {user_id} no existe"
            )
        
        etapas = self.repository.get_etapas_by_usuario(user_id, only_active=only_active)
        return [EtapaAprobadorDetailResponse.model_validate(ea) for ea in etapas]
