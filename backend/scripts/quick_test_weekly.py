"""Quick test: verify weekly summary query and email sending"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from db.engine import SessionLocal
from modules.weekly_summary.repository import get_pending_solicitudes_for_user, get_user_by_id
from modules.weekly_summary.service import weekly_summary_service
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

print(f"User IDs: {settings.WEEKLY_SUMMARY_USER_IDS}")
print(f"Enabled: {settings.WEEKLY_SUMMARY_ENABLED}")

db = SessionLocal()
try:
    for uid in settings.WEEKLY_SUMMARY_USER_IDS:
        user = get_user_by_id(db, uid)
        if user:
            sols = get_pending_solicitudes_for_user(db, uid)
            print(f"\nUser {uid} ({user.full_name}, {user.email}): {len(sols)} pendientes")
            for s in sols:
                etapa = s.stage.label if s.stage else "N/A"
                estado = s.state.label if s.state else "N/A"
                print(f"  - [{s.id}] {s.title} | etapa={etapa} | estado={estado}")
        else:
            print(f"\nUser {uid}: NO ENCONTRADO")

    print("\n--- Enviando correos ---")
    results = weekly_summary_service.run_for_users(db=db, user_ids=settings.WEEKLY_SUMMARY_USER_IDS)
    for uid, res in results.items():
        print(f"  User {uid}: {res}")
finally:
    db.close()

print("\nDone.")
