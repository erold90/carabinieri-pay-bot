#!/usr/bin/env python3
import os
import subprocess

print("🔍 VERIFICA CORREZIONI")
print("=" * 50)

errors = []

# 1. Verifica main.py
print("\n1️⃣ Verifica main.py...")
with open('main.py', 'r') as f:
    content = f.read()
    if 'test_save_command' in content:
        errors.append("test_save_command ancora presente in main.py")
    else:
        print("   ✅ main.py OK")

# 2. Verifica import date
print("\n2️⃣ Verifica import date...")
with open('handlers/service_handler.py', 'r') as f:
    content = f.read()
    if 'from datetime import' in content and ', date' in content:
        print("   ✅ Import date OK")
    else:
        errors.append("Import date mancante in service_handler.py")

# 3. Verifica file deploy
print("\n3️⃣ Verifica file deploy...")
if os.path.exists('.deploy_check'):
    print("   ✅ File .deploy_check presente")
else:
    errors.append("File .deploy_check mancante")

# 4. Test connessione bot
print("\n4️⃣ Test token bot...")
token = os.getenv('BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
if token:
    print(f"   ✅ Token trovato: {token[:10]}...{token[-5:]}")
else:
    errors.append("BOT_TOKEN non trovato")

# Risultato
print("\n" + "=" * 50)
if errors:
    print("❌ ERRORI TROVATI:")
    for err in errors:
        print(f"   - {err}")
else:
    print("✅ TUTTE LE VERIFICHE PASSATE!")
    print("🚀 Il bot dovrebbe funzionare ora")
    print("\n📱 VAI SU TELEGRAM E PROVA:")
    print("   1. Invia /start al bot")
    print("   2. Se non risponde, controlla i log su Railway")

