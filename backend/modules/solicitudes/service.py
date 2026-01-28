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
from core.email import email_service


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
            
            # Enviar notificación a los aprobadores de la primera etapa
            from db.models import EtapaAprobador
            
            aprobadores = self.repository.db.query(EtapaAprobador)\
                .filter(EtapaAprobador.etapa_id == solicitud_data.stage_id)\
                .all()
            
            # Obtener emails de los aprobadores
            emails_aprobadores = []
            for aprobador_rel in aprobadores:
                user = self.user_repository.get_by_id(aprobador_rel.user_id)
                if user and user.email:
                    emails_aprobadores.append(user.email)
            
            # Obtener información del creador y etapa
            creador = self.user_repository.get_by_id(created_by_user_id)
            etapa = self.etapa_repository.get_by_id(solicitud_data.stage_id)
            
            # Enviar notificación
            if emails_aprobadores:
                email_service.send_approval_notification(
                    to_emails=emails_aprobadores,
                    solicitud_id=solicitud.id,
                    solicitud_title=solicitud.title,
                    stage_name=etapa.label if etapa else "Primera etapa",
                    creator_name=creador.full_name if creador else "Creador"
                )
            
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
    
    def solicitar_ajustes(self, solicitud_id: int, comment: str, actor_user_id: int) -> SolicitudDetailResponse:
        """
        Solicitar ajustes en una solicitud
        
        Args:
            solicitud_id: ID de la solicitud
            comment: Comentario explicando los ajustes necesarios
            actor_user_id: ID del usuario que solicita los ajustes
            
        Returns:
            Solicitud actualizada
            
        Raises:
            HTTPException: Si la solicitud no existe o hay error al actualizar
        """
        from db.models import SolicitudEvento, EventAction
        from datetime import datetime
        
        # Obtener solicitud
        solicitud = self.repository.get_by_id(solicitud_id, include_relations=True)
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud con ID {solicitud_id} no encontrada"
            )
        
        # Buscar estado "AJUSTES_SOLICITADOS"
        estado_ajustes = self.estado_repository.get_by_code("AJUSTES_SOLICITADOS")
        if not estado_ajustes:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Estado 'AJUSTES_SOLICITADOS' no encontrado en el sistema"
            )
        
        # Actualizar estado de la solicitud directamente en el objeto
        solicitud.status_id = estado_ajustes.id
        solicitud.updated_at = datetime.utcnow()
        self.repository.db.commit()
        self.repository.db.refresh(solicitud)
        
        # Registrar evento en solicitud_eventos
        evento = SolicitudEvento(
            solicitud_id=solicitud_id,
            stage_id=solicitud.stage_id,
            status_id=estado_ajustes.id,
            actor_user_id=actor_user_id,
            action=EventAction.REQUEST_CHANGES,
            comment=comment,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.repository.db.add(evento)
        self.repository.db.commit()
        
        # Enviar notificación al creador
        creador = self.user_repository.get_by_id(solicitud.created_by_user_id)
        revisor = self.user_repository.get_by_id(actor_user_id)
        if creador and creador.email:
            email_service.send_adjustment_request_notification(
                to_email=creador.email,
                solicitud_id=solicitud.id,
                solicitud_title=solicitud.title,
                comment=comment,
                reviewer_name=revisor.full_name if revisor else "Revisor"
            )
        
        # Recargar con relaciones
        solicitud_actualizada = self.repository.get_by_id(solicitud_id, include_relations=True)
        
        return SolicitudDetailResponse.model_validate(solicitud_actualizada)
    
    def get_eventos_by_solicitud(self, solicitud_id: int) -> List[dict]:
        """
        Obtener historial de eventos de una solicitud
        
        Args:
            solicitud_id: ID de la solicitud
            
        Returns:
            Lista de eventos con información del actor
            
        Raises:
            HTTPException: Si la solicitud no existe
        """
        from db.models import SolicitudEvento
        from sqlalchemy.orm import joinedload
        
        # Verificar que la solicitud existe
        if not self.repository.get_by_id(solicitud_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud con ID {solicitud_id} no encontrada"
            )
        
        # Obtener eventos con información del actor
        eventos = self.repository.db.query(SolicitudEvento)\
            .options(
                joinedload(SolicitudEvento.actor),
                joinedload(SolicitudEvento.state),
                joinedload(SolicitudEvento.stage)
            )\
            .filter(SolicitudEvento.solicitud_id == solicitud_id)\
            .order_by(SolicitudEvento.created_at.asc())\
            .all()
        
        # Formatear respuesta
        return [
            {
                "id": evento.id,
                "action": evento.action.value,
                "comment": evento.comment,
                "created_at": evento.created_at.isoformat(),
                "actor": {
                    "id": evento.actor.id,
                    "full_name": evento.actor.full_name,
                    "email": evento.actor.email
                },
                "state": {
                    "id": evento.state.id,
                    "code": evento.state.code,
                    "label": evento.state.label
                },
                "stage": {
                    "id": evento.stage.id,
                    "code": evento.stage.code,
                    "label": evento.stage.label
                }
            }
            for evento in eventos
        ]
    
    def aprobar_solicitud(
        self, 
        solicitud_id: int, 
        comment: Optional[str], 
        actor_user_id: int
    ) -> SolicitudDetailResponse:
        """
        Aprobar una solicitud y avanzar a la siguiente etapa del flujo
        
        Args:
            solicitud_id: ID de la solicitud a aprobar
            comment: Comentario opcional del aprobador
            actor_user_id: ID del usuario que aprueba
            
        Returns:
            Solicitud actualizada con la nueva etapa
            
        Raises:
            HTTPException: Si la solicitud no existe, si el usuario no es aprobador,
                          o si hay error en la actualización
        """
        from db.models import SolicitudEvento, EventAction, EtapaAprobador
        
        # Obtener la solicitud actual
        solicitud = self.repository.get_by_id(solicitud_id, include_relations=True)
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud con ID {solicitud_id} no encontrada"
            )
        
        # Verificar que el usuario es aprobador de la etapa actual
        aprobador = self.repository.db.query(EtapaAprobador)\
            .filter(
                EtapaAprobador.etapa_id == solicitud.stage_id,
                EtapaAprobador.user_id == actor_user_id
            )\
            .first()
        
        if not aprobador:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para aprobar en esta etapa"
            )
        
        # Buscar la siguiente etapa por orden dentro del mismo área
        from db.models import Etapa
        
        etapa_actual = self.etapa_repository.get_by_id(solicitud.stage_id)
        etapa_actual_id = solicitud.stage_id  # Guardar el ID de la etapa donde se aprobó
        
        # Verificar si la etapa actual requiere aprobación de TODOS (approval_mode: "ALL")
        if etapa_actual.approval_mode == "ALL":
            # Contar cuántos aprobadores hay en esta etapa
            total_aprobadores = self.repository.db.query(EtapaAprobador)\
                .filter(EtapaAprobador.etapa_id == solicitud.stage_id)\
                .count()
            
            # Contar cuántos ya aprobaron (incluyendo esta aprobación)
            aprobaciones_actuales = self.repository.db.query(SolicitudEvento)\
                .filter(
                    SolicitudEvento.solicitud_id == solicitud_id,
                    SolicitudEvento.stage_id == solicitud.stage_id,
                    SolicitudEvento.action == EventAction.APPROVED
                )\
                .count()
            
            # Si aún faltan aprobaciones, registrar evento pero NO avanzar de etapa
            if aprobaciones_actuales + 1 < total_aprobadores:
                evento = SolicitudEvento(
                    solicitud_id=solicitud_id,
                    action=EventAction.APPROVED,
                    comment=comment,
                    actor_user_id=actor_user_id,
                    status_id=solicitud.status_id,  # Mantener el estado actual
                    stage_id=etapa_actual_id
                )
                self.repository.db.add(evento)
                self.repository.db.commit()
                
                # Retornar sin avanzar de etapa
                solicitud_actualizada = self.repository.get_by_id(solicitud_id, include_relations=True)
                return SolicitudDetailResponse.model_validate(solicitud_actualizada)
        
        # Si llegamos aquí, podemos avanzar (o es approval_mode: "ANY" o todos ya aprobaron)
        siguiente_etapa = self.repository.db.query(Etapa)\
            .filter(
                Etapa.area_id == solicitud.area_id,
                Etapa.order == etapa_actual.order + 1
            )\
            .first()
        
        # Determinar el nuevo estado y etapa
        if siguiente_etapa:
            # Hay más etapas: avanzar a la siguiente y mantener EN_REVISION
            nuevo_estado_id = 1  # EN_REVISION
            nueva_etapa_id = siguiente_etapa.id
        else:
            # No hay más etapas: marcar como APROBADO_FINAL
            nuevo_estado_id = 4  # APROBADO_FINAL
            nueva_etapa_id = solicitud.stage_id  # Mantener en la última etapa
        
        # Actualizar la solicitud
        solicitud_update = SolicitudUpdate(
            status_id=nuevo_estado_id,
            stage_id=nueva_etapa_id
        )
        solicitud_actualizada = self.repository.update(solicitud_id, solicitud_update)
        
        # Registrar el evento de aprobación con la etapa DONDE SE APROBÓ (no la nueva)
        evento = SolicitudEvento(
            solicitud_id=solicitud_id,
            action=EventAction.APPROVED,
            comment=comment,
            actor_user_id=actor_user_id,
            status_id=nuevo_estado_id,
            stage_id=etapa_actual_id  # La etapa donde se aprobó, no la nueva
        )
        self.repository.db.add(evento)
        self.repository.db.commit()
        
        # Obtener información del aprobador
        aprobador_user = self.user_repository.get_by_id(actor_user_id)
        
        # Enviar notificación al creador
        creador = self.user_repository.get_by_id(solicitud.created_by_user_id)
        if creador and creador.email:
            email_service.send_approval_notification_to_creator(
                to_email=creador.email,
                solicitud_id=solicitud.id,
                solicitud_title=solicitud.title,
                approver_name=aprobador_user.full_name if aprobador_user else "Aprobador",
                stage_name=etapa_actual.label,
                is_final=(nuevo_estado_id == 4)
            )
        
        # Si hay siguiente etapa, notificar a los nuevos aprobadores
        if siguiente_etapa:
            # Obtener aprobadores de la nueva etapa
            nuevos_aprobadores = self.repository.db.query(EtapaAprobador)\
                .filter(EtapaAprobador.etapa_id == siguiente_etapa.id)\
                .all()
            
            # Obtener emails de los aprobadores
            emails_aprobadores = []
            for aprobador_rel in nuevos_aprobadores:
                user = self.user_repository.get_by_id(aprobador_rel.user_id)
                if user and user.email:
                    emails_aprobadores.append(user.email)
            
            # Enviar notificación a los nuevos aprobadores
            if emails_aprobadores:
                email_service.send_approval_notification(
                    to_emails=emails_aprobadores,
                    solicitud_id=solicitud.id,
                    solicitud_title=solicitud.title,
                    stage_name=siguiente_etapa.label,
                    creator_name=creador.full_name if creador else "Creador"
                )
        
        # Retornar la solicitud actualizada con relaciones
        solicitud_actualizada = self.repository.get_by_id(solicitud_id, include_relations=True)
        return SolicitudDetailResponse.model_validate(solicitud_actualizada)
    
    def rechazar_solicitud(
        self, 
        solicitud_id: int, 
        comment: str, 
        actor_user_id: int
    ) -> SolicitudDetailResponse:
        """
        Rechazar una solicitud
        
        Args:
            solicitud_id: ID de la solicitud a rechazar
            comment: Comentario explicando el motivo del rechazo
            actor_user_id: ID del usuario que rechaza
            
        Returns:
            Solicitud actualizada con estado rechazado
            
        Raises:
            HTTPException: Si la solicitud no existe o si el usuario no es aprobador
        """
        from db.models import SolicitudEvento, EventAction, EtapaAprobador
        
        # Obtener la solicitud actual
        solicitud = self.repository.get_by_id(solicitud_id, include_relations=True)
        if not solicitud:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Solicitud con ID {solicitud_id} no encontrada"
            )
        
        # Verificar que el usuario es aprobador de la etapa actual
        aprobador = self.repository.db.query(EtapaAprobador)\
            .filter(
                EtapaAprobador.etapa_id == solicitud.stage_id,
                EtapaAprobador.user_id == actor_user_id
            )\
            .first()
        
        if not aprobador:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para rechazar en esta etapa"
            )
        
        # Actualizar la solicitud a estado RECHAZADO (id: 3)
        solicitud_update = SolicitudUpdate(
            status_id=3  # RECHAZADO
        )
        self.repository.update(solicitud_id, solicitud_update)
        
        # Registrar el evento de rechazo
        evento = SolicitudEvento(
            solicitud_id=solicitud_id,
            action=EventAction.REJECTED,
            comment=comment,
            actor_user_id=actor_user_id,
            status_id=3,  # RECHAZADO
            stage_id=solicitud.stage_id  # Etapa donde se rechazó
        )
        self.repository.db.add(evento)
        self.repository.db.commit()
        
        # Enviar notificación al creador
        creador = self.user_repository.get_by_id(solicitud.created_by_user_id)
        revisor = self.user_repository.get_by_id(actor_user_id)
        if creador and creador.email:
            email_service.send_rejection_notification(
                to_email=creador.email,
                solicitud_id=solicitud.id,
                solicitud_title=solicitud.title,
                comment=comment,
                reviewer_name=revisor.full_name if revisor else "Revisor"
            )
        
        # Retornar la solicitud actualizada con relaciones
        solicitud_actualizada = self.repository.get_by_id(solicitud_id, include_relations=True)
        return SolicitudDetailResponse.model_validate(solicitud_actualizada)
