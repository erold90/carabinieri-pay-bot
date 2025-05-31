#!/usr/bin/env python3
"""Aggiunge campi missione al database"""
from sqlalchemy import text
from database.connection import engine

print("🔧 AGGIORNAMENTO DATABASE")

try:
    with engine.connect() as conn:
        # Aggiungi campi a services
        conn.execute(text("""
            ALTER TABLE services 
            ADD COLUMN IF NOT EXISTS distance_km INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS has_free_meals BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS has_free_lodging BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS meals_documented INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS ticket_cost FLOAT DEFAULT 0,
            ADD COLUMN IF NOT EXISTS toll_cost FLOAT DEFAULT 0
        """))
        conn.commit()
        
        print("✅ Campi aggiunti al database")
        
except Exception as e:
    print(f"⚠️ {e}")

