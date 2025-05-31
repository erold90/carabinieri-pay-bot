#!/usr/bin/env python3
"""Verifica variabili ambiente"""
import os

print("🔍 VARIABILI AMBIENTE")
print("=" * 50)

important_vars = ['DATABASE_URL', 'BOT_TOKEN', 'TELEGRAM_BOT_TOKEN', 'ENV', 'TZ']

for var in important_vars:
    value = os.getenv(var)
    if value:
        if 'TOKEN' in var:
            print(f"✅ {var}: {value[:10]}...{value[-5:]}")
        elif 'DATABASE' in var:
            print(f"✅ {var}: {value[:30]}...")
        else:
            print(f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: NON IMPOSTATO")

print("\nTutte le variabili:")
for key in sorted(os.environ.keys()):
    if any(x in key.upper() for x in ['TOKEN', 'DATABASE', 'RAILWAY', 'BOT']):
        print(f"  {key}")
