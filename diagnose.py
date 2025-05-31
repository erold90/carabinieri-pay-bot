#!/usr/bin/env python3

print("🔍 DIAGNOSTICA DETTAGLIATA")
print("=" * 50)

# 1. Cerca test_save_command in main.py
print("\n1️⃣ Ricerca 'test_save_command' in main.py:")
with open('main.py', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines, 1):
        if 'test_save_command' in line:
            print(f"   Linea {i}: {line.strip()}")

# 2. Mostra imports in service_handler.py
print("\n2️⃣ Import statements in service_handler.py:")
with open('handlers/service_handler.py', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[:30], 1):  # Prime 30 righe
        if 'import' in line and 'datetime' in line:
            print(f"   Linea {i}: {line.strip()}")

# 3. Cerca tutti gli usi di 'date' in service_handler.py
print("\n3️⃣ Uso di 'date' in service_handler.py:")
with open('handlers/service_handler.py', 'r') as f:
    content = f.read()
    lines = content.split('\n')
    for i, line in enumerate(lines, 1):
        if 'date(' in line and 'update' not in line.lower():
            print(f"   Linea {i}: {line.strip()[:80]}...")
            
print("\n" + "=" * 50)
