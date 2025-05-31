#!/usr/bin/env python3

print("🔍 VERIFICA FINALE")
print("=" * 50)

# 1. Controlla main.py
print("\n1️⃣ Controllo main.py...")
with open('main.py', 'r') as f:
    content = f.read()
    if 'test_save_command' in content:
        print("   ❌ ERRORE: test_save_command ancora presente!")
        # Mostra dove
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'test_save_command' in line:
                print(f"      Linea {i}: {line.strip()}")
    else:
        print("   ✅ OK: test_save_command rimosso")

# 2. Controlla service_handler.py
print("\n2️⃣ Controllo service_handler.py...")
with open('handlers/service_handler.py', 'r') as f:
    found = False
    for i, line in enumerate(f, 1):
        if 'from datetime import' in line:
            print(f"   Linea {i}: {line.strip()}")
            if ', date' in line or 'date,' in line:
                print("   ✅ OK: import date presente")
                found = True
            break
    
    if not found:
        print("   ❌ ERRORE: import date mancante")

# 3. Test rapido Python
print("\n3️⃣ Test sintassi Python...")
import ast
try:
    with open('main.py', 'r') as f:
        ast.parse(f.read())
    print("   ✅ main.py: sintassi OK")
except SyntaxError as e:
    print(f"   ❌ main.py: errore sintassi - {e}")

try:
    with open('handlers/service_handler.py', 'r') as f:
        ast.parse(f.read())
    print("   ✅ service_handler.py: sintassi OK")
except SyntaxError as e:
    print(f"   ❌ service_handler.py: errore sintassi - {e}")

print("\n" + "=" * 50)
print("Se tutto è ✅, il bot dovrebbe funzionare!")
