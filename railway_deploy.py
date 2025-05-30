#!/usr/bin/env python3
import subprocess
import json
import os

def run_command(cmd, shell=True):
    """Esegue comando"""
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

print("🚂 Railway Deploy Helper")
print("=" * 50)

# Verifica railway CLI
print("\n1️⃣ Verifico Railway CLI...")
success, stdout, stderr = run_command("railway --version")

if not success:
    print("❌ Railway CLI non installato!")
    print("\nInstalla con: brew install railway")
    print("O visita: https://docs.railway.app/develop/cli")
    exit(1)

print(f"✅ Railway CLI: {stdout.strip()}")

# Verifica login
print("\n2️⃣ Verifico login Railway...")
success, stdout, stderr = run_command("railway whoami")

if not success:
    print("⚠️  Non sei loggato su Railway")
    print("Esegui: railway login")
    exit(1)

print(f"✅ Loggato come: {stdout.strip()}")

# Menu opzioni
print("\n📋 OPZIONI DEPLOY:")
print("1. Deploy manuale (git push)")
print("2. Visualizza logs")
print("3. Visualizza variabili ambiente")
print("4. Restart servizio")
print("5. Database backup command")

choice = input("\nScegli opzione (1-5): ")

if choice == "1":
    print("\n🚀 Deploy tramite Git push...")
    print("Railway detecta automaticamente i push su GitHub")
    
    # Check uncommitted changes
    success, stdout, _ = run_command("git status --porcelain")
    if stdout.strip():
        print("\n⚠️  Hai modifiche non committate!")
        print("Usa prima: python3 git_update.py")
    else:
        print("\n✅ Pronto per deploy!")
        print("Esegui: git push origin main")
        print("\nRailway deployerà automaticamente!")

elif choice == "2":
    print("\n📜 Visualizzo logs...")
    print("Esegui: railway logs")
    
elif choice == "3":
    print("\n🔐 Variabili ambiente necessarie:")
    print("- BOT_TOKEN")
    print("- DATABASE_URL (auto-configurato)")
    print("- TZ=Europe/Rome")
    print("- ENV=production")
    print("\nVisualizza con: railway variables")
    
elif choice == "4":
    print("\n🔄 Restart servizio...")
    print("Esegui: railway up --detach")
    
elif choice == "5":
    print("\n💾 Backup database:")
    print("railway run pg_dump \$DATABASE_URL > backup_$(date +%Y%m%d).sql")

print("\n" + "=" * 50)
print("📚 Documentazione: https://docs.railway.app")
