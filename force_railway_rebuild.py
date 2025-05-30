#!/usr/bin/env python3
import subprocess
import time

print("🔧 FORZA RAILWAY A RICOSTRUIRE")
print("=" * 50)

# 1. Modifica runtime.txt per forzare rebuild
print("1️⃣ Modifica runtime.txt...")
with open('runtime.txt', 'r') as f:
    content = f.read().strip()

print(f"   Versione attuale: {content}")

# Cambia temporaneamente versione
new_version = "python-3.11.8" if content == "python-3.11.7" else "python-3.11.7"
with open('runtime.txt', 'w') as f:
    f.write(new_version)

print(f"   Nuova versione: {new_version}")

# 2. Aggiungi un commento a main.py con timestamp
print("\n2️⃣ Aggiungi timestamp a main.py...")
with open('main.py', 'r') as f:
    lines = f.readlines()

# Aggiungi commento con timestamp dopo lo shebang
timestamp = f"# Deploy forzato: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
if len(lines) > 1:
    lines.insert(1, timestamp)

with open('main.py', 'w') as f:
    f.writelines(lines)

print(f"   Aggiunto: {timestamp.strip()}")

# 3. Crea file di controllo
print("\n3️⃣ Crea file di controllo...")
with open('.deploy_check', 'w') as f:
    f.write(f"Deploy verificato: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("Se vedi questo file, il deploy è aggiornato.\n")

# 4. Commit tutto
print("\n4️⃣ Commit modifiche...")
subprocess.run("git add -A", shell=True)
subprocess.run(f'git commit -m "force: rebuild completo Railway - {time.strftime('%H:%M:%S')}"', shell=True)

# 5. Push
print("\n5️⃣ Push a GitHub...")
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ MODIFICHE INVIATE!")
print("\n🚀 Railway dovrebbe ora:")
print("   1. Rilevare il cambio di runtime")
print("   2. Fare un rebuild completo")
print("   3. Usare la versione corretta")
print("\n⏰ Attendi 2-3 minuti per il rebuild completo")

# 6. Dopo 10 secondi, ripristina runtime.txt
print("\n⏳ Attendo 10 secondi prima di ripristinare...")
time.sleep(10)

print("\n6️⃣ Ripristino runtime.txt originale...")
with open('runtime.txt', 'w') as f:
    f.write(content)

subprocess.run("git add runtime.txt", shell=True)
subprocess.run('git commit -m "restore: runtime.txt originale"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n✅ Runtime ripristinato")
print("🎯 Railway farà un secondo deploy con la versione corretta")

# Auto-elimina
import os
os.remove(__file__)
print("\n🗑️ Script eliminato")
