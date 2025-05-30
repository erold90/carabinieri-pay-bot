#!/usr/bin/env python3
import os
import subprocess

print("🔧 Fix problemi rimanenti")
print("=" * 50)

# 1. Rimuovi vecchi script di fix che non servono più
old_scripts = [
    "add_clean_chat_feature.py",
    "implementa_pulizia_messaggi_completa.py",
    "fix_rank_buttons_and_clean_chat.py",
    "fix_main_handlers.py",
    "main_updated.py",
    "fix_main_indentation.py",
    "audit_and_fix_all_handlers.py",
    "cleanup_project.py",
    "verify_cleanup.py"
]

print("\n1️⃣ Rimuovo vecchi script di fix...")
removed = []
for script in old_scripts:
    if os.path.exists(script):
        os.remove(script)
        removed.append(script)
        print(f"   ✅ Rimosso: {script}")

if removed:
    subprocess.run(f"git rm {' '.join(removed)}", shell=True, capture_output=True)

# 2. Verifica che holidays sia in requirements.txt
print("\n2️⃣ Verifica dipendenze...")
with open('requirements.txt', 'r') as f:
    requirements = f.read()

if 'holidays' not in requirements:
    print("   ⚠️  Aggiungo 'holidays' a requirements.txt")
    with open('requirements.txt', 'a') as f:
        f.write('\nholidays==0.35\n')
    subprocess.run("git add requirements.txt", shell=True)

# 3. Verifica .env.example per Railway
print("\n3️⃣ Verifica variabili ambiente...")
if os.path.exists('.env.example'):
    with open('.env.example', 'r') as f:
        env_content = f.read()
    
    # Assicurati che DATABASE_URL sia commentato correttamente
    if 'DATABASE_URL=' in env_content and not '# Railway fornirà' in env_content:
        print("   ⚠️  Aggiorno .env.example per Railway")
        env_content = env_content.replace(
            'DATABASE_URL=postgresql://user:password@host:port/database',
            '# DATABASE_URL viene fornito automaticamente da Railway'
        )
        with open('.env.example', 'w') as f:
            f.write(env_content)
        subprocess.run("git add .env.example", shell=True)

# 4. Lista finale dei file essenziali
print("\n4️⃣ Struttura finale del progetto:")
print("\n📁 File Python principali:")
subprocess.run("find . -name '*.py' -not -path './.git/*' -not -path './__pycache__/*' | sort", shell=True)

print("\n📁 File di configurazione:")
subprocess.run("ls -la *.txt *.json *.md Procfile .env.example .gitignore 2>/dev/null | grep -v 'ls:'", shell=True)

# 5. Commit finale
print("\n5️⃣ Commit pulizia finale...")
subprocess.run("git add -A", shell=True)
status = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)

if status.stdout.strip():
    subprocess.run('git commit -m "chore: pulizia finale e rimozione script temporanei"', shell=True)
    subprocess.run("git push origin main", shell=True)
    print("✅ Push completato!")
else:
    print("✅ Niente da committare, progetto già pulito!")

print("\n" + "=" * 50)
print("✅ Pulizia completata!")
print("\n📋 Il progetto ora contiene:")
print("- main.py (entry point)")
print("- config/* (configurazioni)")
print("- database/* (modelli e connessione)")  
print("- handlers/* (gestori comandi)")
print("- services/* (logica business)")
print("- utils/* (utilities)")
print("- requirements.txt, Procfile, etc.")
print("\n🚀 Pronto per il deploy su Railway!")
