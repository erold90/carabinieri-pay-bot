#!/usr/bin/env python3
import subprocess

print("🔧 Fix errore sintassi in service_handler.py")
print("=" * 50)

# Leggi il file
with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# Trova e correggi l'errore sulla linea 16
# Cerca la linea con l'import errato
old_line = 'from config.constants import SUPER_HOLIDAYS, OVERTIME_RATES)'
new_line = 'from config.constants import SUPER_HOLIDAYS, OVERTIME_RATES'

if old_line in content:
    content = content.replace(old_line, new_line)
    print("✅ Rimossa parentesi extra")
else:
    # Prova un altro pattern
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'from config.constants import' in line and line.strip().endswith(')'):
            # Rimuovi la parentesi finale se non c'è una parentesi aperta corrispondente
            if line.count('(') < line.count(')'):
                lines[i] = line.rstrip(')')
                print(f"✅ Corretta linea {i+1}: {lines[i]}")
                content = '\n'.join(lines)
                break

# Salva il file corretto
with open('handlers/service_handler.py', 'w') as f:
    f.write(content)

print("✅ File corretto")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add handlers/service_handler.py", shell=True)
subprocess.run('git commit -m "fix: rimossa parentesi extra in import statement"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("🚀 Railway rifarà il deploy automaticamente")
print("⏰ Attendi 1-2 minuti e il bot ripartirà")
