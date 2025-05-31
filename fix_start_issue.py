#!/usr/bin/env python3
import subprocess
import os

print("🔧 FIX PROBLEMA /START")
print("=" * 50)

# 1. Rimuovi ogni residuo di debug
print("\n1️⃣ Pulizia residui debug...")
with open('main.py', 'r') as f:
    content = f.read()

# Rimuovi righe con debug
lines = content.split('\n')
cleaned = []
skip_next = False

for i, line in enumerate(lines):
    if 'Debug handler registrato' in line:
        continue
    if 'async def debug_log' in line:
        skip_next = True
        continue
    if skip_next and line.strip() == '':
        skip_next = False
        continue
    if not skip_next:
        cleaned.append(line)

content = '\n'.join(cleaned)

# 2. Sposta cleanup_middleware DOPO tutti i command handler
print("\n2️⃣ Riordino handler...")
lines = content.split('\n')

# Trova e rimuovi temporaneamente cleanup_middleware
cleanup_line = None
for i, line in enumerate(lines):
    if 'cleanup_middleware' in line and 'application.add_handler' in line:
        cleanup_line = line
        lines[i] = ''
        break

# Trova l'ultimo command handler
last_command_idx = 0
for i, line in enumerate(lines):
    if 'CommandHandler(' in line and 'application.add_handler' in line:
        last_command_idx = i

# Inserisci cleanup_middleware dopo l'ultimo command
if cleanup_line and last_command_idx > 0:
    lines.insert(last_command_idx + 1, '')
    lines.insert(last_command_idx + 2, '    # Clean chat middleware - eseguito DOPO i comandi')
    lines.insert(last_command_idx + 3, cleanup_line.strip())

content = '\n'.join(lines)

# 3. Assicurati che start_command sia il PRIMO handler
print("\n3️⃣ Posiziono /start come primo handler...")
lines = content.split('\n')

# Trova start handler
start_handler_line = None
start_idx = None
for i, line in enumerate(lines):
    if 'CommandHandler("start", start_command)' in line:
        start_handler_line = line
        start_idx = i
        lines[i] = ''
        break

# Trova il primo application.add_handler
first_handler_idx = None
for i, line in enumerate(lines):
    if 'application.add_handler(' in line and line.strip():
        first_handler_idx = i
        break

# Inserisci start come primo
if start_handler_line and first_handler_idx:
    lines.insert(first_handler_idx, '    # Start command - DEVE essere il primo!')
    lines.insert(first_handler_idx + 1, start_handler_line.strip())
    lines.insert(first_handler_idx + 2, '')

content = '\n'.join(lines)

# Salva
with open('main.py', 'w') as f:
    f.write(content)

print("✅ main.py sistemato")

# 4. Verifica start_handler.py
print("\n4️⃣ Verifica start_handler.py...")
with open('handlers/start_handler.py', 'r') as f:
    start_content = f.read()

# Aggiungi un log semplice all'inizio di start_command
if 'logger.info("Start command received"' not in start_content:
    lines = start_content.split('\n')
    
    # Aggiungi import logging se manca
    if 'import logging' not in start_content:
        for i, line in enumerate(lines):
            if 'from' in line or 'import' in line:
                continue
            else:
                lines.insert(i, 'import logging')
                lines.insert(i+1, '')
                lines.insert(i+2, 'logger = logging.getLogger(__name__)')
                lines.insert(i+3, '')
                break
    
    # Aggiungi log in start_command
    for i, line in enumerate(lines):
        if 'async def start_command(update: Update' in line:
            # Salta docstring
            j = i + 1
            while j < len(lines) and ('"""' in lines[j] or lines[j].strip() == ''):
                j += 1
            
            lines.insert(j, '    logger.info("Start command received")')
            break
    
    start_content = '\n'.join(lines)
    
    with open('handlers/start_handler.py', 'w') as f:
        f.write(start_content)
    
    print("✅ Aggiunto logging in start_handler.py")

# Push
print("\n📤 Push fix...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: riordinati handler - start command ora è primo e cleanup_middleware è dopo i comandi"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n✅ FIX COMPLETATO!")
print("\nIl bot ora dovrebbe:")
print("1. Processare /start come PRIMO handler")
print("2. Eseguire cleanup DOPO aver processato i comandi")
print("3. Loggare 'Start command received' quando riceve /start")

os.remove(__file__)
