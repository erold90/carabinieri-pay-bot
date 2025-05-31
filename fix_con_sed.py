#!/usr/bin/env python3
import subprocess
import os

print("🔧 FIX DIRETTO CON SOSTITUZIONE")
print("=" * 50)

# 1. Fix main.py - elimina la linea con test_save_command
print("\n1️⃣ Fix main.py...")

# Leggi il file
with open('main.py', 'r') as f:
    lines = f.readlines()

# Filtra via la linea problematica
new_lines = [line for line in lines if 'test_save_command' not in line]

# Verifica che abbiamo rimosso qualcosa
if len(new_lines) < len(lines):
    print(f"   ✅ Rimosse {len(lines) - len(new_lines)} linee")
    with open('main.py', 'w') as f:
        f.writelines(new_lines)
else:
    print("   ❌ Nessuna linea rimossa - proviamo con sed")
    # Usa sed come backup
    subprocess.run("sed -i '/test_save_command/d' main.py", shell=True)

# 2. Fix service_handler.py - sostituisci l'import
print("\n2️⃣ Fix service_handler.py...")

with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# Sostituisci l'import
old_line = 'from datetime import datetime, timedelta, time'
new_line = 'from datetime import datetime, timedelta, time, date'

if old_line in content:
    content = content.replace(old_line, new_line)
    print("   ✅ Import aggiornato")
    with open('handlers/service_handler.py', 'w') as f:
        f.write(content)
else:
    print("   ⚠️ Import non trovato nel formato atteso, uso sed")
    subprocess.run("sed -i 's/from datetime import datetime, timedelta, time/from datetime import datetime, timedelta, time, date/g' handlers/service_handler.py", shell=True)

# 3. Doppio controllo con grep
print("\n3️⃣ Verifica con grep...")

# Check test_save_command
result = subprocess.run("grep -n 'test_save_command' main.py", shell=True, capture_output=True, text=True)
if result.stdout:
    print(f"   ❌ test_save_command ancora presente:\n{result.stdout}")
else:
    print("   ✅ test_save_command rimosso")

# Check import date
result = subprocess.run("grep -n 'from datetime import.*date' handlers/service_handler.py", shell=True, capture_output=True, text=True)
if result.stdout:
    print(f"   ✅ Import date presente:\n{result.stdout}")
else:
    print("   ❌ Import date non trovato")

print("\n" + "=" * 50)

# Se ancora ci sono problemi, facciamo una sostituzione brutale
if subprocess.run("grep -q 'test_save_command' main.py", shell=True).returncode == 0:
    print("\n⚠️ APPLICAZIONE FIX BRUTALE...")
    
    # Crea una versione pulita di main.py
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Rimuovi completamente la riga
    lines = content.split('\n')
    clean_lines = []
    for line in lines:
        if 'test_save_command' not in line:
            clean_lines.append(line)
        else:
            print(f"   🗑️ Eliminata: {line}")
    
    with open('main.py', 'w') as f:
        f.write('\n'.join(clean_lines))
    
    print("   ✅ Fix brutale applicato")

# 4. Commit finale
print("\n📤 Commit e push...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: rimozione forzata test_save_command e fix import date"', shell=True)
subprocess.run("git push origin main --force", shell=True)

print("\n✅ FATTO! Il fix è stato applicato forzatamente.")
print("🚀 Attendi il redeploy su Railway")

# Auto-elimina
os.remove(__file__)
