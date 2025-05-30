#!/usr/bin/env python3
import subprocess
import sys
import os

def run_command(cmd, shell=True):
    """Esegue un comando e ritorna output"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

print("🚀 CarabinieriPayBot - Setup Progetto")
print("=" * 50)

# 1. Verifica Python
print("\n1️⃣ Verifico Python...")
success, output = run_command("python3 --version")
if success:
    print(f"✅ Python installato: {output.strip()}")
else:
    print("❌ Python3 non trovato!")
    sys.exit(1)

# 2. Verifica Git
print("\n2️⃣ Verifico Git...")
success, output = run_command("git --version")
if success:
    print(f"✅ Git installato: {output.strip()}")
else:
    print("❌ Git non trovato!")
    sys.exit(1)

# 3. Verifica stato repository
print("\n3️⃣ Verifico repository Git...")
success, output = run_command("git status --porcelain")
if success:
    if output.strip():
        print("⚠️  File modificati non committati:")
        print(output)
    else:
        print("✅ Repository pulito")
else:
    print("❌ Non sei in un repository Git!")
    print("Inizializzo repository...")
    run_command("git init")

# 4. Verifica remote
print("\n4️⃣ Verifico remote GitHub...")
success, output = run_command("git remote -v")
if success and output:
    print("✅ Remote configurato:")
    print(output)
else:
    print("⚠️  Nessun remote configurato")
    print("Usa: git remote add origin https://github.com/TUO_USERNAME/CarabinieriPayBot.git")

# 5. Crea/verifica virtual environment
print("\n5️⃣ Verifico ambiente virtuale...")
if os.path.exists("venv"):
    print("✅ Virtual environment esistente")
else:
    print("📦 Creo virtual environment...")
    success, _ = run_command("python3 -m venv venv")
    if success:
        print("✅ Virtual environment creato")
    else:
        print("❌ Errore creazione venv")

# 6. Verifica file necessari
print("\n6️⃣ Verifico file progetto...")
required_files = [
    "requirements.txt",
    "main.py",
    "config/settings.py",
    "database/models.py"
]

for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} mancante!")

print("\n" + "=" * 50)
print("Setup completato! Prossimi passi:")
print("1. source venv/bin/activate")
print("2. pip install -r requirements.txt")
print("3. Crea .env con BOT_TOKEN e DATABASE_URL")
