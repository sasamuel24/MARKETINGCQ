"""
Clase base declarativa de SQLAlchemy para todos los modelos
"""
from datetime import datetime
from typing import Any
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declarative_base, declared_attr


class CustomBase:
    """
    Clase base con campos comunes para todos los modelos
    """
    
    # ID autoincrementable como primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Timestamps automáticos
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generar automáticamente el nombre de tabla desde el nombre de la clase
        Convierte CamelCase a snake_case y pluraliza
        """
        import re
        # Convertir de CamelCase a snake_case
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
        
        # Pluralizar (agregar 's' al final) - simplificado
        if not name.endswith('s'):
            name += 's'
            
        return name
    
    def dict(self) -> dict[str, Any]:
        """
        Convertir modelo a diccionario
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }


# Base declarativa para todos los modelos
Base = declarative_base(cls=CustomBase)
