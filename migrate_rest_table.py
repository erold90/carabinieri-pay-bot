#!/usr/bin/env python3
"""
Migrazione database per aggiungere tabella riposi
"""
from database.connection import engine, Base
from database.models import Rest

print("🔄 Migrazione database per gestione riposi...")

try:
    # Crea la nuova tabella
    Rest.__table__.create(engine, checkfirst=True)
    print("✅ Tabella 'rests' creata con successo!")
except Exception as e:
    print(f"❌ Errore: {e}")
