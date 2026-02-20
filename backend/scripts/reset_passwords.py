"""
Script para resetear contraseñas de todos los usuarios a una temporal
y activar must_change_password = True
"""
import sys
import os

# Asegurarse de estar en el directorio correcto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security import get_password_hash
from db.session import SessionLocal
from db.models import User

TEMP_PASSWORD = "CafeQuindio2026!"

def reset_all_passwords():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        hashed = get_password_hash(TEMP_PASSWORD)
        
        count = 0
        for user in users:
            user.password_hash = hashed
            user.must_change_password = True
            count += 1
        
        db.commit()
        print(f"✓ {count} usuario(s) actualizados.")
        print(f"  Contraseña temporal: {TEMP_PASSWORD}")
        print(f"  must_change_password = True en todos")
        
        print("\nUsuarios afectados:")
        for user in users:
            print(f"  - [{user.id}] {user.email}")
            
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    reset_all_passwords()
