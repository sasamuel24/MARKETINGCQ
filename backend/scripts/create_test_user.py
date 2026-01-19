"""
Script para crear usuario de prueba

Ejecutar desde el directorio backend:
python scripts/create_test_user.py
"""
import sys
import os

# Agregar el directorio padre al path para poder importar los módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import User, Role, Area
from core.security import get_password_hash


def create_test_user():
    """Crear usuario de prueba para login"""
    db: Session = SessionLocal()
    
    try:
        # Verificar si el usuario ya existe
        existing_user = db.query(User).filter(User.email == "user@example.com").first()
        if existing_user:
            print("✓ El usuario user@example.com ya existe")
            print(f"  ID: {existing_user.id}")
            print(f"  Nombre: {existing_user.full_name}")
            print(f"  Email: {existing_user.email}")
            return
        
        # Obtener o crear un rol por defecto
        role = db.query(Role).first()
        if not role:
            print("× No hay roles en la base de datos. Creando rol 'Usuario'...")
            role = Role(nombre="Usuario")
            db.add(role)
            db.commit()
            db.refresh(role)
            print(f"✓ Rol creado con ID: {role.id}")
        
        # Obtener o crear un área por defecto
        area = db.query(Area).first()
        if not area:
            print("× No hay áreas en la base de datos. Creando área 'General'...")
            area = Area(nombre="General")
            db.add(area)
            db.commit()
            db.refresh(area)
            print(f"✓ Área creada con ID: {area.id}")
        
        # Crear el usuario de prueba
        hashed_password = get_password_hash("password123")
        
        test_user = User(
            full_name="Usuario de Prueba",
            email="user@example.com",
            password_hash=hashed_password,
            rol_id=role.id,
            area_id=area.id
        )
        
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        print("\n✓ Usuario de prueba creado exitosamente!")
        print(f"  ID: {test_user.id}")
        print(f"  Nombre: {test_user.full_name}")
        print(f"  Email: {test_user.email}")
        print(f"  Rol ID: {test_user.rol_id}")
        print(f"  Área ID: {test_user.area_id}")
        print(f"\n  Credenciales de login:")
        print(f"  Email: user@example.com")
        print(f"  Password: password123")
        
    except Exception as e:
        db.rollback()
        print(f"× Error al crear usuario: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Creando usuario de prueba...")
    create_test_user()
