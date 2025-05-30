#!/usr/bin/env python3
import subprocess
import time

print("🔍 Monitoraggio Bot @CC_pay2_bot")
print("=" * 50)

print("\n📱 ISTRUZIONI:")
print("1. Apri Telegram")
print("2. Cerca @CC_pay2_bot")
print("3. Clicca AVVIA o invia /start")
print("\n" + "=" * 50)

print("\n📊 Logs in tempo reale:")
print("(Invia /start su Telegram e guarda qui cosa succede)")
print("-" * 50)

# Usa il comando corretto per railway
subprocess.run("railway logs", shell=True)
