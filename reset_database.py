#!/usr/bin/env python3
"""Reset completo database - DA USARE SOLO SE NECESSARIO"""
import os
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///test.db')

from database.connection import engine, Base
from database.models import *

print("⚠️  ATTENZIONE: Questo cancellerà tutti i dati!")
response = input("Sei sicuro? (yes/no): ")

if response.lower() == 'yes':
    print("🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("✨ Creating new tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset completato!")
else:
    print("❌ Operazione annullata")
