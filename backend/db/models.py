"""
Repositorio base con operaciones CRUD genéricas y modelos SQLAlchemy
"""
import enum
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session, relationship
from sqlalchemy import select, update, delete, Column, String, Integer, ForeignKey, Boolean, UniqueConstraint, Index, Enum

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
    
    # Foreign Keys
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    area_id = Column(Integer, ForeignKey("areas.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Relaciones
    rol = relationship("Role", back_populates="users")
    area = relationship("Area", back_populates="users")
    
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
    
    # Relación
    area = relationship("Area", back_populates="etapas")
    
    __table_args__ = (
        UniqueConstraint('area_id', 'code', name='uq_etapas_area_code'),
        UniqueConstraint('area_id', 'order', name='uq_etapas_area_order'),
        Index('ix_etapas_area_code', 'area_id', 'code'),
        Index('ix_etapas_area_order', 'area_id', 'order'),
    )
    
    def __repr__(self) -> str:
        return f"<Etapa(id={self.id}, area_id={self.area_id}, code='{self.code}', label='{self.label}', order={self.order})>"
