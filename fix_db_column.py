#!/usr/bin/env python3
"""Fix colonna rest_replaced_id"""
import os
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL')

from sqlalchemy import text
from database.connection import engine

print("🔧 Fix database - rimozione rest_replaced_id")

try:
    with engine.connect() as conn:
        # Rimuovi foreign key se esiste
        conn.execute(text("ALTER TABLE services DROP CONSTRAINT IF EXISTS services_rest_replaced_id_fkey"))
        conn.commit()
        
        # Rimuovi colonna
        conn.execute(text("ALTER TABLE services DROP COLUMN IF EXISTS rest_replaced_id"))
        conn.commit()
        
        print("✅ Colonna rimossa")
except Exception as e:
    print(f"⚠️ {e}")
    print("La colonna potrebbe non esistere o essere già stata rimossa")
