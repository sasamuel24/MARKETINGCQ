import sys, os
sys.path.insert(0, r'C:/desarollos/MARKETINGCQ/backend')
os.chdir(r'C:/desarollos/MARKETINGCQ/backend')
from db.engine import engine
from sqlalchemy import text

with engine.connect() as con:
    exists = con.execute(text('SELECT id FROM etapa_aprobadores WHERE etapa_id=7 AND user_id=10')).fetchone()
    if exists:
        print('Ya existe, no se inserta')
    else:
        con.execute(text('INSERT INTO etapa_aprobadores (etapa_id, user_id, created_at, updated_at) VALUES (7, 10, NOW(), NOW())'))
        con.commit()
        print('Adrian Quintero agregado a PROD_E2 (etapa_id=7)')

    rows = con.execute(text(
        'SELECT ea.user_id, u.full_name, e.code FROM etapa_aprobadores ea '
        'JOIN etapas e ON ea.etapa_id=e.id JOIN usuarios u ON ea.user_id=u.id WHERE ea.etapa_id=7'
    ))
    print('Aprobadores actuales de PROD_E2:')
    for r in rows:
        print(' ', dict(r._mapping))
