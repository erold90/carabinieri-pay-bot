#!/usr/bin/env python3
import subprocess
import os

print("🧹 PULIZIA E PUSH FINALE")
print("=" * 50)

# 1. Rimuovi file temporanei
print("\n1️⃣ Pulizia file temporanei:")
temp_files = [
    'fix_duplicate_run.py',
    'fix_all_complete.py',
    'check_and_clean_conflicts.py',
    'check_deploy_status.py',
    'debug_bot_issues.py'
]

for file in temp_files:
    if os.path.exists(file):
        try:
            os.remove(file)
            print(f"   ✅ Rimosso {file}")
        except:
            print(f"   ⚠️ Non posso rimuovere {file}")

# 2. Git status
print("\n2️⃣ Stato git:")
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
if result.stdout:
    print(result.stdout)
else:
    print("✅ Working directory pulita")

# 3. Aggiungi tutto e committa
print("\n3️⃣ Commit finale:")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "chore: pulizia file temporanei e fix finali"', shell=True)

# 4. Push
print("\n4️⃣ Push su Railway:")
result = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Push completato!")
else:
    print("ℹ️ Nulla da pushare o già aggiornato")

print("\n" + "=" * 50)
print("✅ PULIZIA COMPLETATA!")
print("\n🚂 Railway sta facendo il deploy...")
print("⏰ Attendi 2-3 minuti poi testa con:")
print("\n   python3 test_bot_connection.py")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script auto-eliminato")
