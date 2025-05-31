#!/usr/bin/env python3
"""Verifica struttura database"""
import os
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///test.db')

from database.connection import engine, Base
from database.models import *
from sqlalchemy import inspect

print("🔍 Verifica database...")

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tabelle trovate: {tables}")
    
    required = ['users', 'services', 'overtimes', 'travel_sheets', 'leaves', 'rests']
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"⚠️ Tabelle mancanti: {missing}")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelle create")
    else:
        print("✅ Tutte le tabelle OK")
except Exception as e:
    print(f"❌ Errore: {e}")
