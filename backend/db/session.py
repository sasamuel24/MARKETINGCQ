"""
Manejo de sesiones de base de datos
"""
from typing import Generator
from sqlalchemy.orm import Session

from db.engine import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener sesión de base de datos.
    Se usa como dependencia en FastAPI endpoints.
    
    Ejemplo:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session de SQLAlchemy
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
