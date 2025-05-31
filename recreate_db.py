#!/usr/bin/env python3
"""Script per ricreare le tabelle del database se necessario"""
from database.connection import engine, Base, init_db
from database.models import User, Service, Overtime, TravelSheet, Leave, Rest

print("🔄 Ricreazione tabelle database...")

try:
    # Inizializza database
    init_db()
    print("✅ Database inizializzato correttamente")
except Exception as e:
    print(f"❌ Errore: {e}")
    print("Provo a ricreare le tabelle...")
    
    try:
        # Drop e ricrea
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelle ricreate")
    except Exception as e2:
        print(f"❌ Errore ricreazione: {e2}")
