"""
Servicio de etapas - Lógica de negocio
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from modules.etapas.repository import EtapaRepository
from modules.etapas.schemas import EtapaCreate, EtapaUpdate, EtapaResponse, EtapaDetailResponse
from modules.areas.repository import AreaRepository


class EtapaService:
    """Servicio para gestionar la lógica de negocio de etapas"""
    
    def __init__(self, db: Session):
        self.repository = EtapaRepository(db)
        self.area_repository = AreaRepository(db)
    
    def get_etapa_by_id(self, etapa_id: int) -> EtapaDetailResponse:
        """
        Obtener etapa por ID con información del área
        
        Args:
            etapa_id: ID de la etapa
            
        Returns:
            Etapa encontrada
            
        Raises:
            HTTPException: Si la etapa no existe
        """
        etapa = self.repository.get_by_id(etapa_id, include_relations=True)
        if not etapa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Etapa con ID {etapa_id} no encontrada"
            )
        return EtapaDetailResponse.model_validate(etapa)
    
    def get_all_etapas(
        self, 
        skip: int = 0, 
        limit: int = 100,
        area_id: Optional[int] = None,
        only_active: bool = False
    ) -> tuple[List[EtapaDetailResponse], int]:
        """
        Obtener todas las etapas con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            area_id: Filtrar por área (opcional)
            only_active: Si True, solo retorna etapas activas
            
        Returns:
            Tupla con (lista de etapas, total de etapas)
        """
        etapas = self.repository.get_all(
            skip=skip, 
            limit=limit, 
            area_id=area_id,
            only_active=only_active,
            include_relations=True
        )
        total = self.repository.count(area_id=area_id, only_active=only_active)
        return [EtapaDetailResponse.model_validate(etapa) for etapa in etapas], total
    
    def create_etapa(self, etapa_data: EtapaCreate) -> EtapaDetailResponse:
        """
        Crear una nueva etapa
        
        Args:
            etapa_data: Datos de la etapa a crear
            
        Returns:
            Etapa creada
            
        Raises:
            HTTPException: Si el área no existe o si code/order ya existen en el área
        """
        # Verificar que el área existe
        if not self.area_repository.exists(etapa_data.area_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El área con ID {etapa_data.area_id} no existe"
            )
        
        # Verificar si el código ya existe en el área
        if self.repository.exists_by_area_and_code(etapa_data.area_id, etapa_data.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una etapa con el código '{etapa_data.code}' en el área {etapa_data.area_id}"
            )
        
        # Verificar si el orden ya existe en el área
        if self.repository.exists_by_area_and_order(etapa_data.area_id, etapa_data.order):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una etapa con el orden {etapa_data.order} en el área {etapa_data.area_id}"
            )
        
        try:
            etapa = self.repository.create(etapa_data)
            # Recargar con relaciones
            etapa = self.repository.get_by_id(etapa.id, include_relations=True)
            return EtapaDetailResponse.model_validate(etapa)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error de integridad al crear la etapa. Verifique que code y order sean únicos en el área."
            )
    
    def update_etapa(self, etapa_id: int, etapa_data: EtapaUpdate) -> EtapaDetailResponse:
        """
        Actualizar una etapa existente
        
        Args:
            etapa_id: ID de la etapa a actualizar
            etapa_data: Datos a actualizar
            
        Returns:
            Etapa actualizada
            
        Raises:
            HTTPException: Si la etapa no existe o si code/order ya existen en el área
        """
        # Verificar que la etapa existe
        etapa_actual = self.repository.get_by_id(etapa_id)
        if not etapa_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Etapa con ID {etapa_id} no encontrada"
            )
        
        # Verificar si el nuevo código ya existe en el área (excluyendo la etapa actual)
        if etapa_data.code and self.repository.exists_by_area_and_code(
            etapa_actual.area_id, 
            etapa_data.code, 
            exclude_id=etapa_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una etapa con el código '{etapa_data.code}' en el área {etapa_actual.area_id}"
            )
        
        # Verificar si el nuevo orden ya existe en el área (excluyendo la etapa actual)
        if etapa_data.order is not None and self.repository.exists_by_area_and_order(
            etapa_actual.area_id, 
            etapa_data.order, 
            exclude_id=etapa_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe una etapa con el orden {etapa_data.order} en el área {etapa_actual.area_id}"
            )
        
        try:
            etapa = self.repository.update(etapa_id, etapa_data)
            if not etapa:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Etapa con ID {etapa_id} no encontrada"
                )
            # Recargar con relaciones
            etapa = self.repository.get_by_id(etapa.id, include_relations=True)
            return EtapaDetailResponse.model_validate(etapa)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error de integridad al actualizar la etapa. Verifique que code y order sean únicos en el área."
            )
    
    def delete_etapa(self, etapa_id: int) -> None:
        """
        Eliminar una etapa
        
        Args:
            etapa_id: ID de la etapa a eliminar
            
        Raises:
            HTTPException: Si la etapa no existe
        """
        if not self.repository.delete(etapa_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Etapa con ID {etapa_id} no encontrada"
            )
    
    def get_etapas_by_area(self, area_id: int, only_active: bool = True) -> List[EtapaResponse]:
        """
        Obtener todas las etapas de un área
        
        Args:
            area_id: ID del área
            only_active: Si True, solo retorna etapas activas
            
        Returns:
            Lista de etapas ordenadas por order
        """
        etapas = self.repository.get_by_area(area_id, only_active=only_active)
        return [EtapaResponse.model_validate(etapa) for etapa in etapas]
