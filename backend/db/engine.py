"""
Configuración del motor de base de datos SQLAlchemy
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings


# Crear engine de SQLAlchemy
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_pre_ping=True,  # Verificar conexiones antes de usarlas
    pool_size=5,  # Tamaño del pool de conexiones
    max_overflow=10  # Conexiones adicionales permitidas
)

# Crear SessionLocal
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)
