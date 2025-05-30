#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()

# Verifica che le variabili siano caricate
print("🔍 Verifica configurazione ambiente")
print("=" * 40)

db_url = os.getenv('DATABASE_URL') or os.getenv('TELEGRAM_DATABASE_URL')
bot_token = os.getenv('BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')

print(f"DATABASE_URL: {'✅ Configurato' if db_url else '❌ Mancante'}")
print(f"BOT_TOKEN: {'✅ Configurato' if bot_token else '❌ Mancante'}")

if not db_url:
    print("\n⚠️ Per test locale, crea un file .env con:")
    print("DATABASE_URL=sqlite:///test.db")
    print("BOT_TOKEN=test")
else:
    print("\n✅ Configurazione OK per test!")
    print("\nEsegui: python3 test_database.py")
