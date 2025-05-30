#!/usr/bin/env python3
import subprocess
import time
from datetime import datetime

def run_command(cmd, shell=True):
    """Esegue comando"""
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

print("🤖 CarabinieriPayBot - Status Check")
print("=" * 50)
print(f"⏰ Check time: {datetime.now().strftime('%H:%M:%S')}")

# 1. Check Railway logs
print("\n📊 Ultimi logs Railway:")
print("-" * 30)
success, stdout, stderr = run_command("railway logs --tail 10")
if success and stdout:
    # Mostra solo le ultime righe rilevanti
    lines = stdout.strip().split('\n')
    for line in lines[-10:]:
        if any(keyword in line.lower() for keyword in ['error', 'starting', 'bot', 'connected', 'webhook']):
            print(line)

# 2. Bot info
print("\n🤖 Info Bot:")
print("-" * 30)
print("Nome Bot: @CarabinieriPayBot")
print("Token: 8183773514:AAH...")

# 3. Test checklist
print("\n✅ Checklist Test:")
print("-" * 30)
print("1. Apri Telegram")
print("2. Cerca @CarabinieriPayBot")
print("3. Invia /start")
print("4. Dovresti vedere il menu principale")

print("\n📱 Comandi disponibili:")
print("-" * 30)
commands = [
    "/start - Menu principale",
    "/nuovo - Registra nuovo servizio",
    "/scorta - Registra servizio scorta",
    "/straordinari - Gestione straordinari",
    "/fv - Fogli viaggio",
    "/licenze - Gestione licenze",
    "/mese - Report mensile",
    "/oggi - Riepilogo oggi",
    "/ieri - Riepilogo ieri",
    "/export - Export Excel",
    "/impostazioni - Configurazione"
]

for cmd in commands:
    print(f"  {cmd}")

print("\n🔧 Troubleshooting:")
print("-" * 30)
print("Se il bot non risponde:")
print("1. railway logs --tail 50  (controlla errori)")
print("2. railway restart         (riavvia servizio)")
print("3. railway variables       (verifica variabili)")

print("\n📊 Monitoraggio continuo:")
print("-" * 30)
print("railway logs --tail -f")

print("\n" + "=" * 50)

# Chiedi se vuole vedere i logs live
show_logs = input("\nVuoi vedere i logs in tempo reale? (s/n): ").lower()
if show_logs == 's':
    print("\n📊 Logs in tempo reale (Ctrl+C per uscire):")
    print("-" * 50)
    subprocess.run("railway logs --tail -f", shell=True)
