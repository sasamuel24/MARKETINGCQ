"""
Servicio de áreas - Lógica de negocio
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from modules.areas.repository import AreaRepository
from modules.areas.schemas import AreaCreate, AreaUpdate, AreaResponse


class AreaService:
    """Servicio para gestionar la lógica de negocio de áreas"""
    
    def __init__(self, db: Session):
        self.repository = AreaRepository(db)
    
    def get_area_by_id(self, area_id: int) -> AreaResponse:
        """
        Obtener área por ID
        
        Args:
            area_id: ID del área
            
        Returns:
            Área encontrada
            
        Raises:
            HTTPException: Si el área no existe
        """
        area = self.repository.get_by_id(area_id)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Área con ID {area_id} no encontrada"
            )
        return AreaResponse.model_validate(area)
    
    def get_all_areas(self, skip: int = 0, limit: int = 100) -> tuple[List[AreaResponse], int]:
        """
        Obtener todas las áreas con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            
        Returns:
            Tupla con (lista de áreas, total de áreas)
        """
        areas = self.repository.get_all(skip=skip, limit=limit)
        total = self.repository.count()
        return [AreaResponse.model_validate(area) for area in areas], total
    
    def create_area(self, area_data: AreaCreate) -> AreaResponse:
        """
        Crear una nueva área
        
        Args:
            area_data: Datos del área a crear
            
        Returns:
            Área creada
            
        Raises:
            HTTPException: Si el nombre ya existe
        """
        # Verificar si el nombre ya existe
        if self.repository.exists_by_nombre(area_data.nombre):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un área con el nombre '{area_data.nombre}'"
            )
        
        try:
            area = self.repository.create(area_data)
            return AreaResponse.model_validate(area)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un área con el nombre '{area_data.nombre}'"
            )
    
    def update_area(self, area_id: int, area_data: AreaUpdate) -> AreaResponse:
        """
        Actualizar un área existente
        
        Args:
            area_id: ID del área a actualizar
            area_data: Datos a actualizar
            
        Returns:
            Área actualizada
            
        Raises:
            HTTPException: Si el área no existe o el nuevo nombre ya está en uso
        """
        # Verificar que el área existe
        if not self.repository.exists(area_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Área con ID {area_id} no encontrada"
            )
        
        # Verificar si el nuevo nombre ya existe (excluyendo el área actual)
        if area_data.nombre and self.repository.exists_by_nombre(area_data.nombre, exclude_id=area_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un área con el nombre '{area_data.nombre}'"
            )
        
        try:
            area = self.repository.update(area_id, area_data)
            if not area:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Área con ID {area_id} no encontrada"
                )
            return AreaResponse.model_validate(area)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un área con el nombre '{area_data.nombre}'"
            )
    
    def delete_area(self, area_id: int) -> None:
        """
        Eliminar un área
        
        Args:
            area_id: ID del área a eliminar
            
        Raises:
            HTTPException: Si el área no existe
        """
        if not self.repository.delete(area_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Área con ID {area_id} no encontrada"
            )
    
    def get_area_by_nombre(self, nombre: str) -> Optional[AreaResponse]:
        """
        Obtener área por nombre
        
        Args:
            nombre: Nombre del área
            
        Returns:
            Área encontrada o None
        """
        area = self.repository.get_by_nombre(nombre)
        if area:
            return AreaResponse.model_validate(area)
        return None
