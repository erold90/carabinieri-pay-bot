#!/usr/bin/env python3
import subprocess
import sys

def run_command(cmd, shell=True):
    """Esegue comando"""
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

print("🚂 Setup Variabili Railway")
print("=" * 50)

# Verifica se siamo collegati a un progetto Railway
print("\n1️⃣ Verifico collegamento Railway...")
success, stdout, stderr = run_command("railway status")

if not success or "No project" in stderr:
    print("❌ Non sei collegato a un progetto Railway!")
    print("\nCollegati con:")
    print("railway link")
    sys.exit(1)

print("✅ Progetto Railway collegato")

# Mostra variabili attuali
print("\n2️⃣ Variabili attualmente configurate:")
success, stdout, stderr = run_command("railway variables")
if success:
    print(stdout)
else:
    print("Nessuna variabile configurata")

print("\n3️⃣ Configurazione BOT_TOKEN")
print("=" * 30)
print("\nPer ottenere il token del bot:")
print("1. Apri Telegram")
print("2. Cerca @BotFather")
print("3. Invia /mybots")
print("4. Seleziona il tuo bot")
print("5. Clicca 'API Token'")
print("6. Copia il token")

token = input("\nIncolla qui il BOT_TOKEN: ").strip()

if not token or len(token) < 40:
    print("❌ Token non valido!")
    sys.exit(1)

# Imposta le variabili su Railway
print("\n4️⃣ Configurazione variabili su Railway...")

commands = [
    f'railway variables set BOT_TOKEN="{token}"',
    'railway variables set TZ="Europe/Rome"',
    'railway variables set ENV="production"'
]

for cmd in commands:
    print(f"\n🔄 {cmd}")
    success, stdout, stderr = run_command(cmd)
    if success:
        print("✅ Impostata")
    else:
        print(f"❌ Errore: {stderr}")

print("\n5️⃣ Verifica finale...")
success, stdout, stderr = run_command("railway variables")
if success:
    print("\n📋 Variabili configurate:")
    print(stdout)

print("\n" + "=" * 50)
print("✅ Configurazione completata!")
print("\n🚀 Railway farà il redeploy automaticamente")
print("📊 Monitora con: railway logs --tail")

# Chiedi se vuole forzare il redeploy
redeploy = input("\nVuoi forzare il redeploy ora? (s/n): ").lower()
if redeploy == 's':
    print("\n🔄 Redeploy in corso...")
    run_command("railway up --detach")
    print("✅ Redeploy avviato!")
