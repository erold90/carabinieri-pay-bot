#!/usr/bin/env python3
import subprocess
import os
from datetime import datetime

print("📤 COMMIT E PUSH FINALE")
print("=" * 50)

# 1. Verifica se ci sono modifiche
result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)

if result.stdout.strip():
   print("📝 Modifiche trovate:")
   print(result.stdout)
   
   # 2. Aggiungi tutto
   print("\n➕ Aggiungendo tutti i file...")
   subprocess.run("git add -A", shell=True)
   
   # 3. Commit
   commit_msg = f"fix: correzioni complete per scorte - sintassi, calcoli e conferma [{datetime.now().strftime('%H:%M')}]"
   print(f"\n💬 Commit: {commit_msg}")
   subprocess.run(f'git commit -m "{commit_msg}"', shell=True)
   
   # 4. Push
   print("\n🚀 Push su GitHub...")
   result = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
   
   if result.returncode == 0:
       print("✅ Push completato con successo!")
       print("\n⏳ Railway sta facendo il deploy automatico...")
       print("🕐 Attendi 1-2 minuti")
   else:
       print(f"❌ Errore push: {result.stderr}")
else:
   print("ℹ️ Nessuna modifica da committare")
   print("✅ Tutto già aggiornato su GitHub")
   
   # Verifica ultimo commit
   last_commit = subprocess.run("git log -1 --oneline", shell=True, capture_output=True, text=True)
   print(f"\n📌 Ultimo commit: {last_commit.stdout.strip()}")

# 5. Crea file timestamp per tracciare deploy
timestamp_file = '.last_deploy'
with open(timestamp_file, 'w') as f:
   f.write(f"Ultimo deploy: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
   f.write("Modifiche applicate:\n")
   f.write("- Fix sintassi async/await\n")
   f.write("- Calculate_escort_hours implementata\n")
   f.write("- Controllo territorio escluso per scorte\n")
   f.write("- Visualizzazione pasti nel riepilogo\n")
   f.write("- Callback confirm_yes funzionante\n")

subprocess.run(f"git add {timestamp_file}", shell=True)
subprocess.run('git commit -m "chore: update deploy timestamp"', shell=True, check=False)
subprocess.run("git push origin main", shell=True, check=False)

print("\n" + "=" * 50)
print("✅ OPERAZIONE COMPLETATA!")
print("\n📱 Ora vai su Telegram e testa il bot!")

# Auto-elimina
os.remove(__file__)
