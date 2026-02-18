"""
Script de prueba para verificar el envío del correo semanal de resumen.

Ejecutar desde la carpeta backend:
    py scripts/test_weekly_summary.py

Este script:
1. Conecta a la base de datos
2. Ejecuta la query de solicitudes pendientes para los usuarios configurados
3. Muestra los resultados en consola
4. Envía el correo de resumen semanal
"""
import sys
import os
import logging

# Agregar el directorio padre al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from db.engine import SessionLocal
from modules.weekly_summary.repository import get_pending_solicitudes_for_user, get_user_by_id
from modules.weekly_summary.service import weekly_summary_service

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


def print_separator():
    print("=" * 70)


def test_query_solicitudes(db, user_id: int):
    """Prueba la query de solicitudes pendientes para un usuario."""
    print_separator()
    usuario = get_user_by_id(db, user_id)
    if not usuario:
        print(f"❌ Usuario con ID {user_id} NO encontrado en la base de datos.")
        return
    
    print(f"👤 Usuario: {usuario.full_name} (id={usuario.id}, email={usuario.email})")
    
    solicitudes = get_pending_solicitudes_for_user(db, user_id)
    
    if not solicitudes:
        print(f"   ℹ️  No tiene solicitudes pendientes de aprobación.")
        return
    
    print(f"   📋 Solicitudes pendientes: {len(solicitudes)}")
    print()
    
    for i, s in enumerate(solicitudes, 1):
        from datetime import datetime
        dias = (datetime.utcnow() - s.created_at).days
        alerta = " ⚠️ URGENTE" if dias > 7 else ""
        print(f"   {i}. [{s.id}] {s.title}")
        print(f"      Área: {s.area.nombre if s.area else 'N/A'}")
        print(f"      Etapa: {s.stage.label if s.stage else 'N/A'}")
        print(f"      Estado: {s.state.label if s.state else 'N/A'}")
        print(f"      Creado por: {s.created_by.full_name if s.created_by else 'N/A'}")
        print(f"      Creado: {s.created_at.strftime('%Y-%m-%d %H:%M')} ({dias} día(s)){alerta}")
        print()


def test_send_emails(db):
    """Ejecuta el servicio completo de envío de correos."""
    print_separator()
    print("📧 ENVIANDO CORREOS DE RESUMEN SEMANAL...")
    print(f"   Usuarios objetivo: {settings.WEEKLY_SUMMARY_USER_IDS}")
    print()
    
    results = weekly_summary_service.run_for_users(
        db=db,
        user_ids=settings.WEEKLY_SUMMARY_USER_IDS,
    )
    
    print()
    print("📊 RESULTADOS DEL ENVÍO:")
    for user_id, result in results.items():
        status_icon = {
            "sent": "✅",
            "skipped": "⏭️",
            "error": "❌",
            "email_failed": "⚠️",
        }.get(result.get("status", ""), "❓")
        
        print(f"   {status_icon} User ID {user_id}: {result}")
    
    return results


def main():
    print()
    print_separator()
    print("🧪 TEST: Resumen Semanal de Artes Pendientes")
    print(f"   Scheduler habilitado: {settings.WEEKLY_SUMMARY_ENABLED}")
    print(f"   Día programado: {settings.WEEKLY_CRON_DAY}")
    print(f"   Hora programada: {settings.WEEKLY_CRON_HOUR}:{settings.WEEKLY_CRON_MINUTE:02d}")
    print(f"   Usuarios objetivo: {settings.WEEKLY_SUMMARY_USER_IDS}")
    print(f"   FRONTEND_URL: {settings.FRONTEND_URL}")
    print_separator()
    
    db = SessionLocal()
    try:
        # Fase 1: Verificar query de solicitudes
        print("\n📌 FASE 1: Verificando solicitudes pendientes por usuario\n")
        for user_id in settings.WEEKLY_SUMMARY_USER_IDS:
            test_query_solicitudes(db, user_id)
        
        # Fase 2: Preguntar si enviar correos
        print_separator()
        respuesta = input("\n¿Deseas enviar los correos de prueba? (s/n): ").strip().lower()
        
        if respuesta in ("s", "si", "yes", "y"):
            results = test_send_emails(db)
        else:
            print("\n⏭️  Envío de correos omitido.")
        
    except Exception as e:
        logger.error(f"Error en test: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
    finally:
        db.close()
    
    print()
    print_separator()
    print("🏁 Test finalizado.")
    print_separator()


if __name__ == "__main__":
    main()
