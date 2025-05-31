#!/usr/bin/env python3
import os

token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
if token:
    print(f"✅ Token trovato: {token[:20]}...")
    print(f"   Lunghezza: {len(token)} caratteri")
    if len(token) < 40:
        print("⚠️  Token sembra troppo corto!")
else:
    print("❌ TOKEN NON TROVATO!")
    print("   Verifica su Railway: Settings → Variables → BOT_TOKEN")
