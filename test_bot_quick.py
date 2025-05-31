#!/usr/bin/env python3
"""Test rapido del bot"""
import os
import sys

# Verifica variabili ambiente
print("🔍 VERIFICA AMBIENTE")
print("=" * 50)

token = os.getenv('BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
db_url = os.getenv('DATABASE_URL')

if not token:
    print("❌ BOT_TOKEN non trovato!")
    sys.exit(1)
else:
    print(f"✅ Token: {token[:10]}...{token[-5:]}")

if not db_url:
    print("⚠️  DATABASE_URL non trovato (userò SQLite)")
else:
    print(f"✅ Database: {db_url[:30]}...")

# Test import
print("\n🔍 TEST IMPORT")
print("=" * 50)

try:
    from database.connection import SessionLocal, init_db
    print("✅ Database imports OK")
except Exception as e:
    print(f"❌ Database import error: {e}")

try:
    from handlers.start_handler import start_command
    print("✅ Handler imports OK")
except Exception as e:
    print(f"❌ Handler import error: {e}")

print("\n✅ Test completato!")
