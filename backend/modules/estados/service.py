"""
Servicio de estados - Lógica de negocio
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from modules.estados.repository import EstadoRepository
from modules.estados.schemas import EstadoCreate, EstadoUpdate, EstadoResponse


class EstadoService:
    """Servicio para gestionar la lógica de negocio de estados"""
    
    def __init__(self, db: Session):
        self.repository = EstadoRepository(db)
    
    def get_estado_by_id(self, estado_id: int) -> EstadoResponse:
        """
        Obtener estado por ID
        
        Args:
            estado_id: ID del estado
            
        Returns:
            Estado encontrado
            
        Raises:
            HTTPException: Si el estado no existe
        """
        estado = self.repository.get_by_id(estado_id)
        if not estado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estado con ID {estado_id} no encontrado"
            )
        return EstadoResponse.model_validate(estado)
    
    def get_all_estados(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        only_active: bool = False
    ) -> tuple[List[EstadoResponse], int]:
        """
        Obtener todos los estados con paginación
        
        Args:
            skip: Número de registros a saltar
            limit: Límite de registros a retornar
            only_active: Si True, solo retorna estados activos
            
        Returns:
            Tupla con (lista de estados, total de estados)
        """
        estados = self.repository.get_all(skip=skip, limit=limit, only_active=only_active)
        total = self.repository.count(only_active=only_active)
        return [EstadoResponse.model_validate(estado) for estado in estados], total
    
    def create_estado(self, estado_data: EstadoCreate) -> EstadoResponse:
        """
        Crear un nuevo estado
        
        Args:
            estado_data: Datos del estado a crear
            
        Returns:
            Estado creado
            
        Raises:
            HTTPException: Si el código ya existe
        """
        # Verificar si el código ya existe
        if self.repository.exists_by_code(estado_data.code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un estado con el código '{estado_data.code}'"
            )
        
        try:
            estado = self.repository.create(estado_data)
            return EstadoResponse.model_validate(estado)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un estado con el código '{estado_data.code}'"
            )
    
    def update_estado(self, estado_id: int, estado_data: EstadoUpdate) -> EstadoResponse:
        """
        Actualizar un estado existente
        
        Args:
            estado_id: ID del estado a actualizar
            estado_data: Datos a actualizar
            
        Returns:
            Estado actualizado
            
        Raises:
            HTTPException: Si el estado no existe o el nuevo código ya está en uso
        """
        # Verificar que el estado existe
        if not self.repository.exists(estado_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estado con ID {estado_id} no encontrado"
            )
        
        # Verificar si el nuevo código ya existe (excluyendo el estado actual)
        if estado_data.code and self.repository.exists_by_code(estado_data.code, exclude_id=estado_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un estado con el código '{estado_data.code}'"
            )
        
        try:
            estado = self.repository.update(estado_id, estado_data)
            if not estado:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Estado con ID {estado_id} no encontrado"
                )
            return EstadoResponse.model_validate(estado)
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un estado con el código '{estado_data.code}'"
            )
    
    def delete_estado(self, estado_id: int) -> None:
        """
        Eliminar un estado
        
        Args:
            estado_id: ID del estado a eliminar
            
        Raises:
            HTTPException: Si el estado no existe
        """
        if not self.repository.delete(estado_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Estado con ID {estado_id} no encontrado"
            )
    
    def get_estado_by_code(self, code: str) -> Optional[EstadoResponse]:
        """
        Obtener estado por código
        
        Args:
            code: Código del estado
            
        Returns:
            Estado encontrado o None
        """
        estado = self.repository.get_by_code(code)
        if estado:
            return EstadoResponse.model_validate(estado)
        return None
    
    def get_final_estados(self) -> List[EstadoResponse]:
        """
        Obtener todos los estados finales activos
        
        Returns:
            Lista de estados finales
        """
        estados = self.repository.get_final_states()
        return [EstadoResponse.model_validate(estado) for estado in estados]
