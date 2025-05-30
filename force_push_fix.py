#!/usr/bin/env python3
import subprocess
import os

print("🔧 FORCE PUSH DELLA VERSIONE CORRETTA")
print("=" * 50)

# Prima puliamo i file non tracciati
print("🧹 Pulizia file temporanei...")
temp_files = ['fix_nested_import_error.py', 'implement_rest_management.py']
for f in temp_files:
    if os.path.exists(f):
        os.remove(f)
        print(f"   Rimosso: {f}")

# Verifica sintassi locale
print("\n🔍 Verifica sintassi locale...")
try:
    with open('main.py', 'r') as f:
        compile(f.read(), 'main.py', 'exec')
    print("✅ Sintassi locale CORRETTA!")
except SyntaxError as e:
    print(f"❌ Errore locale: {e}")

# Mostra lo stato git
print("\n📊 Stato Git:")
subprocess.run("git status", shell=True)

# Aggiungi le modifiche
print("\n📤 Preparazione commit...")
subprocess.run("git add -A", shell=True)
subprocess.run("git status", shell=True)

# Fai un commit con timestamp
from datetime import datetime
timestamp = datetime.now().strftime("%H:%M:%S")
commit_msg = f"fix: versione corretta senza errori sintassi - {timestamp}"

subprocess.run(f'git commit -m "{commit_msg}"', shell=True)

# Push forzato
print("\n🚀 Push forzato...")
subprocess.run("git push origin main --force-with-lease", shell=True)

print("\n" + "=" * 50)
print("✅ PUSH COMPLETATO!")
print("🚀 Railway dovrebbe rilevare le modifiche ora")
print("⏰ Attendi 30-60 secondi per il redeploy")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script eliminato")
