#!/usr/bin/env python3
import subprocess
import sys

def run_command(cmd, shell=True):
    """Esegue comando e ritorna risultato"""
    print(f"🔄 Eseguo: {cmd}")
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Errore: {result.stderr}")
        return False
    if result.stdout:
        print(f"✅ {result.stdout.strip()}")
    return True

print("🚀 Fix automatico + Deploy")
print("=" * 50)

# 1. Fix del file service_handler.py
print("\n1️⃣ Fixo l'import mancante...")

with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# Aggiungi import se mancante
if 'from handlers.start_handler import start_command' not in content:
    # Trova dove inserire l'import (dopo gli altri import from handlers)
    import_position = content.find('from handlers.')
    if import_position == -1:
        # Se non ci sono altri import from handlers, mettilo dopo gli import generali
        import_position = content.find('from services.')
    
    # Trova la fine della riga
    line_end = content.find('\n', import_position)
    
    # Inserisci il nuovo import
    new_import = '\nfrom handlers.start_handler import start_command'
    content = content[:line_end] + new_import + content[line_end:]
    
    # Scrivi il file
    with open('handlers/service_handler.py', 'w') as f:
        f.write(content)
    
    print("✅ Import aggiunto!")
else:
    print("ℹ️  Import già presente")

# 2. Git add
print("\n2️⃣ Aggiungo file modificati...")
if not run_command("git add ."):
    sys.exit(1)

# 3. Git commit
print("\n3️⃣ Creo commit...")
if not run_command('git commit -m "fix: import mancante start_command in service_handler"'):
    print("ℹ️  Nessuna modifica da committare")

# 4. Git push
print("\n4️⃣ Push su GitHub...")
if not run_command("git push origin main"):
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ Deploy completato!")
print("\n📊 Monitoraggio:")
print("railway logs --tail")
print("\n⏰ Railway deployerà automaticamente in 2-3 minuti")
