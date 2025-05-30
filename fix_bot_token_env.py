#!/usr/bin/env python3
import subprocess
import sys

def run_command(cmd, shell=True):
    """Esegue comando"""
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

print("🔧 Fix BOT_TOKEN environment variable")
print("=" * 50)

# Opzione 1: Modifica il codice per usare TELEGRAM_BOT_TOKEN
print("\n1️⃣ Modifico main.py per usare TELEGRAM_BOT_TOKEN...")

with open('main.py', 'r') as f:
    content = f.read()

# Sostituisci BOT_TOKEN con TELEGRAM_BOT_TOKEN
content = content.replace("os.getenv('BOT_TOKEN')", "os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))")

with open('main.py', 'w') as f:
    f.write(content)

print("✅ main.py aggiornato!")

# Aggiorna anche config/settings.py
print("\n2️⃣ Modifico config/settings.py...")

with open('config/settings.py', 'r') as f:
    content = f.read()

content = content.replace("BOT_TOKEN = os.getenv('BOT_TOKEN')", "BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))")

with open('config/settings.py', 'w') as f:
    f.write(content)

print("✅ config/settings.py aggiornato!")

# Git operations
print("\n3️⃣ Commit e push...")
run_command("git add main.py config/settings.py")
run_command('git commit -m "fix: supporto per TELEGRAM_BOT_TOKEN env variable"')
run_command("git push origin main")

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("\n🚀 Railway rifarà il deploy automaticamente")
print("📊 Monitora con: railway logs --tail")
print("\n🎉 Il bot dovrebbe avviarsi correttamente ora!")
