"""
Repositorio base con operaciones CRUD genéricas y modelos SQLAlchemy
"""
import enum
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session, relationship
from sqlalchemy import select, update, delete, Column, String, Integer, ForeignKey, Boolean, UniqueConstraint, Index, Enum, Text, BigInteger, CheckConstraint

from db.base import Base


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Repositorio base con operaciones CRUD estándar
    
    Uso:
        class UserRepository(BaseRepository[User]):
            def __init__(self, db: Session):
                super().__init__(User, db)
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        Args:
            model: Clase del modelo SQLAlchemy
            db: Sesión de base de datos
        """
        self.model = model
        self.db = db
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Obtener un registro por ID
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """
        Obtener todos los registros con paginación opcional
        """
        query = self.db.query(self.model)
        
        # Aplicar filtros si existen
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Contar registros
        """
        query = self.db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()
    
    def create(self, **kwargs) -> ModelType:
        """
        Crear un nuevo registro
        """
        db_obj = self.model(**kwargs)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        Actualizar un registro por ID
        """
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None
        
        for key, value in kwargs.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    def delete(self, id: int) -> bool:
        """
        Eliminar un registro por ID
        """
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False
        
        self.db.delete(db_obj)
        self.db.commit()
        return True
    
    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """
        Obtener un registro por un campo específico
        """
        if not hasattr(self.model, field):
            return None
        return self.db.query(self.model).filter(
            getattr(self.model, field) == value
        ).first()
    
    def exists(self, id: int) -> bool:
        """
        Verificar si existe un registro por ID
        """
        return self.db.query(self.model).filter(self.model.id == id).count() > 0


# ============================================================================
# MODELOS DE BASE DE DATOS
# ============================================================================

class Role(Base):
    """
    Modelo para la tabla de roles de usuarios
    """
    __tablename__ = "roles"
    
    nombre = Column(String(120), nullable=False, unique=True, index=True)
    
    # Relación con usuarios
    users = relationship("User", back_populates="rol")
    
    def __repr__(self) -> str:
        return f"<Role(id={self.id}, nombre='{self.nombre}')>"


class Area(Base):
    """
    Modelo para la tabla de áreas
    """
    __tablename__ = "areas"
    
    nombre = Column(String(120), nullable=False, unique=True, index=True)
    
    # Relación con usuarios
    users = relationship("User", back_populates="area")
    
    # Relación con etapas
    etapas = relationship("Etapa", back_populates="area")
    
    # Relación con solicitudes
    solicitudes = relationship("Solicitud", back_populates="area")
    
    def __repr__(self) -> str:
        return f"<Area(id={self.id}, nombre='{self.nombre}')>"


class User(Base):
    """
    Modelo para la tabla de usuarios
    """
    __tablename__ = "usuarios"
    
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    must_change_password = Column(Boolean, nullable=False, server_default='true')
    
    # Foreign Keys
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Relaciones
    rol = relationship("Role", back_populates="users")
    area = relationship("Area", back_populates="users")
    etapa_aprobaciones = relationship("EtapaAprobador", back_populates="user")
    solicitudes_created = relationship("Solicitud", foreign_keys="[Solicitud.created_by_user_id]", back_populates="created_by")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"


class Estado(Base):
    """
    Modelo para la tabla de estados del flujo de trabajo
    """
    __tablename__ = "estados"
    
    code = Column(String(50), nullable=False, unique=True, index=True)
    label = Column(String(120), nullable=False)
    order = Column(Integer, nullable=False)
    is_final = Column(Boolean, nullable=False, server_default='false')
    is_active = Column(Boolean, nullable=False, server_default='true')
    
    # Relaciones
    solicitudes = relationship("Solicitud", foreign_keys="[Solicitud.status_id]", back_populates="state")
    
    __table_args__ = (
        UniqueConstraint('code', name='uq_estados_code'),
    )
    
    def __repr__(self) -> str:
        return f"<Estado(id={self.id}, code='{self.code}', label='{self.label}', order={self.order})>"


class ApprovalMode(str, enum.Enum):
    """
    Enum para el modo de aprobación de una etapa
    """
    ANY = "ANY"  # Cualquier aprobador puede aprobar
    ALL = "ALL"  # Todos los aprobadores deben aprobar


class Etapa(Base):
    """
    Modelo para la tabla de etapas del flujo de trabajo por área
    """
    __tablename__ = "etapas"
    
    # Foreign Key
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Campos
    code = Column(String(50), nullable=False)
    label = Column(String(120), nullable=False)
    order = Column("order", Integer, nullable=False)  # Especificar nombre de columna explícitamente
    is_active = Column(Boolean, nullable=False, server_default='true')
    approval_mode = Column(Enum(ApprovalMode), nullable=False, server_default='ANY')
    
    # Relaciones
    area = relationship("Area", back_populates="etapas")
    aprobadores = relationship("EtapaAprobador", back_populates="etapa")
    solicitudes = relationship("Solicitud", foreign_keys="[Solicitud.stage_id]", back_populates="stage")
    
    __table_args__ = (
        UniqueConstraint('area_id', 'code', name='uq_etapas_area_code'),
        UniqueConstraint('area_id', 'order', name='uq_etapas_area_order'),
        Index('ix_etapas_area_code', 'area_id', 'code'),
        Index('ix_etapas_area_order', 'area_id', 'order'),
    )
    
    def __repr__(self) -> str:
        return f"<Etapa(id={self.id}, area_id={self.area_id}, code='{self.code}', label='{self.label}', order={self.order})>"


class EtapaAprobador(Base):
    """
    Modelo para la tabla puente de aprobadores por etapa
    """
    __tablename__ = "etapa_aprobadores"
    
    # Foreign Keys
    etapa_id = Column(Integer, ForeignKey("etapas.id", ondelete="RESTRICT"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Campos
    is_active = Column(Boolean, nullable=False, server_default='true')
    
    # Relaciones
    etapa = relationship("Etapa", back_populates="aprobadores")
    user = relationship("User", back_populates="etapa_aprobaciones")
    
    __table_args__ = (
        UniqueConstraint('etapa_id', 'user_id', name='uq_etapa_aprobadores_etapa_user'),
        Index('ix_etapa_aprobadores_etapa_user', 'etapa_id', 'user_id'),
    )
    
    def __repr__(self) -> str:
        return f"<EtapaAprobador(id={self.id}, etapa_id={self.etapa_id}, user_id={self.user_id}, is_active={self.is_active})>"


class Solicitud(Base):
    """
    Modelo para la tabla de solicitudes
    """
    __tablename__ = "solicitudes"
    
    # Campos
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    es_para_cafe = Column(Boolean, nullable=True)  # Solo aplica cuando el área es "Operaciones y Calidad"
    es_para_exportacion = Column(Boolean, nullable=True)  # Si el arte va a exportación (incluye aprobador ID 19)
    
    # Foreign Keys
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="RESTRICT"), nullable=False, index=True)
    stage_id = Column(Integer, ForeignKey("etapas.id", ondelete="RESTRICT"), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey("estados.id", ondelete="RESTRICT"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Relaciones con nombres de dominio
    area = relationship("Area", back_populates="solicitudes")
    stage = relationship("Etapa", foreign_keys=[stage_id], back_populates="solicitudes")
    state = relationship("Estado", foreign_keys=[status_id], back_populates="solicitudes")
    created_by = relationship("User", foreign_keys=[created_by_user_id], back_populates="solicitudes_created")
    files = relationship("SolicitudFile", back_populates="solicitud", cascade="all, delete-orphan")
    eventos = relationship("SolicitudEvento", back_populates="solicitud", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_solicitudes_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<Solicitud(id={self.id}, title='{self.title}', area_id={self.area_id}, stage_id={self.stage_id}, status_id={self.status_id})>"


class SolicitudFile(Base):
    """
    Modelo para la tabla de archivos adjuntos de solicitudes
    """
    __tablename__ = "solicitud_files"
    
    # Foreign Key
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Campos de almacenamiento
    storage_provider = Column(String(50), nullable=False)  # ej: "s3", "local", "gcs"
    storage_path = Column(String(500), nullable=False)     # ruta/llave: "bucket/folder/file.ext"
    filename = Column(String(255), nullable=False)         # nombre original del archivo
    content_type = Column(String(100), nullable=False)     # mime type: "image/png", "application/pdf"
    size_bytes = Column(BigInteger, nullable=False)        # tamaño en bytes
    doc_type = Column(String(50), nullable=False)          # tipo lógico: "ARTE", "BRIEF", "EVIDENCIA"
    
    # Relación
    solicitud = relationship("Solicitud", back_populates="files")
    
    __table_args__ = (
        # Índices para consultas frecuentes
        Index('ix_solicitud_files_solicitud_id', 'solicitud_id'),
        Index('ix_solicitud_files_doc_type', 'doc_type'),
        Index('ix_solicitud_files_created_at', 'created_at'),
        # Evitar duplicados exactos en una solicitud
        UniqueConstraint('solicitud_id', 'storage_path', name='uq_solicitud_files_solicitud_storage'),
        # Validar tamaño positivo
        CheckConstraint('size_bytes >= 0', name='ck_solicitud_files_size_bytes_positive'),
    )
    
    def __repr__(self) -> str:
        return f"<SolicitudFile(id={self.id}, solicitud_id={self.solicitud_id}, filename='{self.filename}', doc_type='{self.doc_type}', size_bytes={self.size_bytes})>"


class EventAction(str, enum.Enum):
    """
    Enum para las acciones de eventos de solicitud
    """
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    COMMENTED = "COMMENTED"
    STAGE_CHANGED = "STAGE_CHANGED"
    REQUEST_CHANGES = "REQUEST_CHANGES"


class SolicitudEvento(Base):
    """
    Modelo para la tabla de eventos/auditoría de solicitudes
    """
    __tablename__ = "solicitud_eventos"
    
    # Foreign Keys
    solicitud_id = Column(Integer, ForeignKey("solicitudes.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_id = Column(Integer, ForeignKey("etapas.id", ondelete="RESTRICT"), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey("estados.id", ondelete="RESTRICT"), nullable=False, index=True)
    actor_user_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Campos
    action = Column(Enum(EventAction), nullable=False)
    comment = Column(Text, nullable=True)
    
    # Relaciones con nombres de dominio
    solicitud = relationship("Solicitud", back_populates="eventos")
    stage = relationship("Etapa", foreign_keys=[stage_id])
    state = relationship("Estado", foreign_keys=[status_id])
    actor = relationship("User", foreign_keys=[actor_user_id])
    
    __table_args__ = (
        Index('ix_solicitud_eventos_solicitud_id', 'solicitud_id'),
        Index('ix_solicitud_eventos_stage_id', 'stage_id'),
        Index('ix_solicitud_eventos_status_id', 'status_id'),
        Index('ix_solicitud_eventos_actor_user_id', 'actor_user_id'),
        Index('ix_solicitud_eventos_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<SolicitudEvento(id={self.id}, solicitud_id={self.solicitud_id}, action='{self.action.value}', actor_user_id={self.actor_user_id})>"
