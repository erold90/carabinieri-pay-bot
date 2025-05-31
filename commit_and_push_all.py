#!/usr/bin/env python3
import subprocess
import os

print("📤 COMMIT E PUSH DI TUTTI I CAMBIAMENTI")
print("=" * 50)

# 1. Verifica stato git
print("\n1️⃣ Stato git attuale:")
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
if result.stdout:
    print(result.stdout)
else:
    print("✅ Nessun file modificato")

# 2. Aggiungi tutti i file
print("\n2️⃣ Aggiungo tutti i file...")
subprocess.run(['git', 'add', '-A'], check=True)

# 3. Verifica cosa stiamo per committare
print("\n3️⃣ File da committare:")
result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
print(result.stdout)

# 4. Commit
print("\n4️⃣ Commit...")
commit_message = "fix: risolti tutti gli errori di import e sintassi, bot pronto per deploy"
result = subprocess.run(['git', 'commit', '-m', commit_message], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Commit creato")
    print(result.stdout)
else:
    print("ℹ️ Niente da committare o errore")
    print(result.stderr)

# 5. Push
print("\n5️⃣ Push su GitHub...")
result = subprocess.run(['git', 'push', 'origin', 'main'], capture_output=True, text=True)
if result.returncode == 0:
    print("✅ Push completato!")
    print(result.stdout)
else:
    print("❌ Errore push:")
    print(result.stderr)

# 6. Verifica deploy
print("\n" + "=" * 50)
print("🚀 FATTO! Railway dovrebbe rilevare i cambiamenti automaticamente")
print("\n📋 Prossimi passi:")
print("1. Attendi 2-3 minuti per il deploy automatico")
print("2. Controlla i log su Railway")
print("3. Prova /start nel bot Telegram")
print("4. Prova /test per verificare il salvataggio")

# Pulizia file temporanei
temp_files = ['check_bot_status.py', 'minimal_bot.py', 'verify_token.py', 
              'test_save_service.py', 'HOLIDAYS_FIX.txt', 'CONVERSATION_STATES.md',
              'FIX_CONVERSATION_HANDLER.txt']

print("\n🧹 Pulizia file temporanei...")
for file in temp_files:
    if os.path.exists(file):
        os.remove(file)
        print(f"   ✅ Rimosso {file}")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script auto-eliminato")
