import sys, os
sys.path.insert(0, r'C:/desarollos/MARKETINGCQ/backend')
os.chdir(r'C:/desarollos/MARKETINGCQ/backend')
from db.engine import engine
from sqlalchemy import text

with engine.connect() as con:
    # Columnas de solicitudes para saber el nombre del campo de estado
    cols = con.execute(text(
        "SELECT column_name FROM information_schema.columns WHERE table_name='solicitudes' ORDER BY ordinal_position"
    ))
    print('Columnas de solicitudes:')
    for c in cols: print(' ', c[0])
