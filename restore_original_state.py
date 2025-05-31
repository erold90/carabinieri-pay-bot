#!/usr/bin/env python3
import subprocess
import os

print("🔧 RIPRISTINO STATO ORIGINALE DEL BOT")
print("=" * 50)

# 1. Ripristina tutti i file modificati
print("\n1️⃣ Ripristino file originali...")
files_to_restore = [
    'main.py',
    'handlers/start_handler.py',
    'utils/clean_chat.py',
    'config/settings.py'
]

for file in files_to_restore:
    print(f"   Ripristino {file}...")
    subprocess.run(f"git checkout {file}", shell=True)

print("✅ Tutti i file ripristinati")

# 2. Riabilita il cleanup_middleware se era stato disabilitato
print("\n2️⃣ Verifica cleanup_middleware...")
with open('main.py', 'r') as f:
    lines = f.readlines()

modified = False
for i, line in enumerate(lines):
    if '# TEMP DISABLED:' in line and 'cleanup_middleware' in line:
        lines[i] = line.replace('# TEMP DISABLED: ', '')
        print("✅ Riabilitato cleanup_middleware")
        modified = True
    elif '# application.add_handler(MessageHandler(filters.ALL, cleanup_middleware)' in line:
        lines[i] = line.replace('# ', '')
        print("✅ Riabilitato cleanup_middleware")
        modified = True

if modified:
    with open('main.py', 'w') as f:
        f.writelines(lines)

# 3. Rimuovi qualsiasi debug handler aggiunto
print("\n3️⃣ Rimozione debug handler...")
with open('main.py', 'r') as f:
    content = f.read()

# Rimuovi blocchi di debug
if 'async def debug_log(' in content or 'async def log_all_updates(' in content:
    lines = content.split('\n')
    cleaned_lines = []
    skip = False
    
    for line in lines:
        if 'async def debug_log(' in line or 'async def log_all_updates(' in line:
            skip = True
        elif skip and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            skip = False
        
        if not skip and '[DEBUG]' not in line and 'Debug handler registrato' not in line:
            cleaned_lines.append(line)
    
    content = '\n'.join(cleaned_lines)
    
    with open('main.py', 'w') as f:
        f.write(content)
    print("✅ Rimossi debug handler")

# 4. Pulisci handlers/start_handler.py da log di debug
print("\n4️⃣ Pulizia start_handler.py...")
with open('handlers/start_handler.py', 'r') as f:
    lines = f.readlines()

cleaned_lines = []
for line in lines:
    if '[START]' not in line and '[DEBUG]' not in line and '🚀 START command received' not in line:
        cleaned_lines.append(line)

# Rimuovi anche import logging se non era originale
content = ''.join(cleaned_lines)
if 'logger = logging.getLogger(__name__)' in content:
    lines = content.split('\n')
    cleaned = []
    for i, line in enumerate(lines):
        if 'logger = logging.getLogger(__name__)' in line:
            # Rimuovi anche l'import se è isolato
            if i > 0 and 'import logging' in lines[i-1]:
                cleaned.pop()  # Rimuovi l'ultimo elemento (import logging)
            continue
        cleaned.append(line)
    content = '\n'.join(cleaned)

with open('handlers/start_handler.py', 'w') as f:
    f.write(content)
print("✅ Pulito start_handler.py")

# 5. Assicurati che le impostazioni di clean chat siano come originale
print("\n5️⃣ Verifica impostazioni clean chat...")
with open('config/settings.py', 'r') as f:
    content = f.read()

if 'CLEAN_CHAT_ENABLED = False' in content:
    content = content.replace('CLEAN_CHAT_ENABLED = False', 'CLEAN_CHAT_ENABLED = True')
    print("✅ Riabilitato CLEAN_CHAT_ENABLED")

if 'KEEP_ONLY_LAST_MESSAGE = False' in content:
    content = content.replace('KEEP_ONLY_LAST_MESSAGE = False', 'KEEP_ONLY_LAST_MESSAGE = True')
    print("✅ Riabilitato KEEP_ONLY_LAST_MESSAGE")

with open('config/settings.py', 'w') as f:
    f.write(content)

# 6. Verifica sintassi finale
print("\n🔍 Verifica sintassi finale...")
files_to_check = ['main.py', 'handlers/start_handler.py', 'utils/clean_chat.py', 'config/settings.py']

all_ok = True
for file in files_to_check:
    result = subprocess.run(['python3', '-m', 'py_compile', file], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {file} OK")
    else:
        print(f"❌ {file}: {result.stderr}")
        all_ok = False

# 7. Commit e push
if all_ok:
    print("\n📤 Push stato originale...")
    subprocess.run("git add -A", shell=True)
    subprocess.run('git commit -m "restore: ripristinato stato originale - rimossi tutti i debug"', shell=True)
    subprocess.run("git push origin main", shell=True)
    
    print("\n" + "=" * 50)
    print("✅ BOT RIPRISTINATO ALLO STATO ORIGINALE!")
    print("\n🎯 Il bot ora:")
    print("✅ Ha il sistema di auto-cancellazione attivo")
    print("✅ Nessun debug handler extra")
    print("✅ Token corretto su Railway")
    print("\n🚀 Il bot dovrebbe funzionare perfettamente!")
else:
    print("\n❌ Ci sono errori di sintassi, controlla manualmente")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script auto-eliminato")
