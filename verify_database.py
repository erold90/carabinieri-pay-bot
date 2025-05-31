#!/usr/bin/env python3
"""Verifica e ricrea tabelle se necessario"""
import os
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///test.db')

from database.connection import engine, Base, init_db
from database.models import *
from sqlalchemy import inspect

print("🔍 Verifica struttura database...")

try:
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    print(f"Tabelle esistenti: {existing_tables}")
    
    # Se manca la tabella rests, creala
    if 'rests' not in existing_tables:
        print("⚠️ Tabella 'rests' mancante, la creo...")
        Rest.__table__.create(engine, checkfirst=True)
        print("✅ Tabella 'rests' creata")
    
    # Verifica tutte le tabelle
    required_tables = ['users', 'services', 'overtimes', 'travel_sheets', 'leaves', 'rests']
    missing = [t for t in required_tables if t not in existing_tables]
    
    if missing:
        print(f"⚠️ Tabelle mancanti: {missing}")
        print("Creo le tabelle mancanti...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelle create")
    else:
        print("✅ Tutte le tabelle presenti")
        
except Exception as e:
    print(f"❌ Errore: {e}")
    print("Provo a ricreare tutto il database...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database ricreato")
    except Exception as e2:
        print(f"❌ Errore critico: {e2}")
