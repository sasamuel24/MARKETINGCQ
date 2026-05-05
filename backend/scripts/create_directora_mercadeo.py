"""
Script para crear el rol DIRECTOR y la usuaria Directora de Mercadeo

Ejecutar desde el directorio backend (con venv activo):
    python scripts/create_directora_mercadeo.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import User, Role, Area
from core.security import get_password_hash


def create_directora():
    db: Session = SessionLocal()

    try:
        # ── 1. Crear rol DIRECTOR si no existe ────────────────────────────
        role = db.query(Role).filter(Role.nombre == "DIRECTOR").first()
        if role:
            print(f"✓ Rol DIRECTOR ya existe (id={role.id})")
        else:
            role = Role(nombre="DIRECTOR")
            db.add(role)
            db.commit()
            db.refresh(role)
            print(f"✓ Rol DIRECTOR creado (id={role.id})")

        # ── 2. Verificar área INNOVACION (id=2) ───────────────────────────
        area = db.query(Area).filter(Area.id == 2).first()
        if not area:
            print("× No se encontró el área con id=2 (INNOVACION). Verifica la BD.")
            return
        print(f"✓ Área encontrada: {area.nombre} (id={area.id})")

        # ── 3. Crear usuaria ──────────────────────────────────────────────
        EMAIL = "directora.mercadeo@cafequindio.com.co"
        existing = db.query(User).filter(User.email == EMAIL).first()
        if existing:
            print(f"\n✓ La usuaria ya existe (ID: {existing.id})")
            print(f"  Nombre:   {existing.full_name}")
            print(f"  Rol ID:   {existing.rol_id}")
            print(f"  Área ID:  {existing.area_id}")
        else:
            usuario = User(
                full_name="Directora de Mercadeo",
                email=EMAIL,
                password_hash=get_password_hash("Mercadeo2024"),
                rol_id=role.id,
                area_id=area.id,
                must_change_password=False,
            )
            db.add(usuario)
            db.commit()
            db.refresh(usuario)
            print(f"\n✓ Usuaria creada exitosamente!")
            print(f"  ID:     {usuario.id}")
            print(f"  Nombre: {usuario.full_name}")
            print(f"  Rol:    DIRECTOR (id={role.id})")
            print(f"  Área:   {area.nombre} (id={area.id})")

        print(f"\n  Credenciales para login:")
        print(f"  Email:    {EMAIL}")
        print(f"  Password: Mercadeo2024")
        print(f"\n  IMPORTANTE: Anota el rol_id={role.id} — úsalo en el .env o config si es necesario.")

    except Exception as e:
        db.rollback()
        print(f"× Error: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("  Creando rol DIRECTOR + Directora de Mercadeo")
    print("=" * 50)
    create_directora()
