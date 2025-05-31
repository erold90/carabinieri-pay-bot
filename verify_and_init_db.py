#!/usr/bin/env python3
"""Verifica e inizializza database"""
import os
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///test.db')

from database.connection import engine, Base, init_db
from sqlalchemy import inspect

print("🔍 Verifica struttura database...")

try:
    init_db()
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"✅ Tabelle trovate: {tables}")
    
    required = ['users', 'services', 'overtimes', 'travel_sheets', 'leaves', 'rests']
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"⚠️ Tabelle mancanti: {missing}")
        print("Creazione in corso...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelle create!")
    else:
        print("✅ Database OK!")
        
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()
