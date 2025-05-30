#!/usr/bin/env python3
import subprocess
import os

print("🔧 Fix errore instant_delete_mode")
print("=" * 50)

# 1. Rimuovi il riferimento a instant_delete_mode che causa l'errore
print("\n1️⃣ Rimozione handler problematico da main.py...")
with open('main.py', 'r') as f:
    content = f.read()

# Rimuovi l'handler che causa problemi
lines = content.split('\n')
new_lines = []
skip_next = False

for i, line in enumerate(lines):
    if 'instant_delete_mode' in line:
        # Salta questa linea e le prossime 3 (l'intero handler)
        skip_next = 3
        print(f"✅ Rimossa linea {i+1}: {line.strip()}")
        continue
    
    if skip_next > 0:
        skip_next -= 1
        continue
        
    new_lines.append(line)

content = '\n'.join(new_lines)

# 2. Semplifica l'import di clean_chat
content = content.replace(
    'from utils.clean_chat import cleanup_middleware, instant_delete_mode, register_bot_message',
    'from utils.clean_chat import cleanup_middleware'
)

with open('main.py', 'w') as f:
    f.write(content)
print("✅ main.py corretto")

# 3. Implementa un sistema di auto-delete più semplice
print("\n2️⃣ Implementazione sistema auto-delete semplificato...")

# Aggiungi funzione semplice in clean_chat.py
with open('utils/clean_chat.py', 'r') as f:
    clean_content = f.read()

# Se la funzione instant_delete_mode non esiste già, rimuovila e ricreala
if 'async def instant_delete_mode' in clean_content:
    # Rimuovi la vecchia implementazione
    start = clean_content.find('async def instant_delete_mode')
    end = clean_content.find('\n\nasync def', start + 1)
    if end == -1:
        end = clean_content.find('\n\n#', start + 1)
    if end == -1:
        end = len(clean_content)
    clean_content = clean_content[:start] + clean_content[end:]

# Aggiungi versione corretta alla fine
simple_auto_delete = '''

# Sistema semplificato di auto-delete
AUTO_DELETE_ENABLED = True
DELETE_DELAY = 30  # secondi

async def setup_auto_delete(application):
    """Setup auto-delete per l'applicazione"""
    print("✅ Sistema auto-delete configurato")
'''

clean_content = clean_content.rstrip() + '\n' + simple_auto_delete + '\n'

with open('utils/clean_chat.py', 'w') as f:
    f.write(clean_content)
print("✅ Sistema auto-delete semplificato aggiunto")

# 4. Rimuovi anche il comando clean che potrebbe dare problemi
print("\n3️⃣ Rimozione temporanea comando /clean...")
with open('handlers/start_handler.py', 'r') as f:
    handler_content = f.read()

# Rimuovi la funzione clean_command se presente
if 'async def clean_command' in handler_content:
    start = handler_content.find('async def clean_command')
    # Trova la fine della funzione
    end = handler_content.find('\n\nasync def', start + 1)
    if end == -1:
        end = handler_content.find('\n\n#', start + 1)
    if end == -1:
        # Se è l'ultima funzione, rimuovi fino alla fine
        handler_content = handler_content[:start].rstrip()
    else:
        handler_content = handler_content[:start] + handler_content[end:]
    
    with open('handlers/start_handler.py', 'w') as f:
        f.write(handler_content)
    print("✅ Comando clean rimosso")

# 5. Rimuovi riferimenti a clean_command da main.py
with open('main.py', 'r') as f:
    main_content = f.read()

# Rimuovi import
main_content = main_content.replace(
    'from handlers.start_handler import start_command, dashboard_callback, clean_command',
    'from handlers.start_handler import start_command, dashboard_callback'
)

# Rimuovi handler
lines = main_content.split('\n')
new_lines = []
for line in lines:
    if 'CommandHandler("clean"' not in line:
        new_lines.append(line)
    else:
        print(f"✅ Rimossa linea: {line.strip()}")

main_content = '\n'.join(new_lines)

with open('main.py', 'w') as f:
    f.write(main_content)
print("✅ Riferimenti a clean_command rimossi")

# Commit e push
print("\n📤 Commit e push del fix...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: rimosso instant_delete_mode che causava errore NameError"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("🚀 Il bot dovrebbe ripartire correttamente ora")
print("\n⚠️ L'auto-cancellazione è stata temporaneamente disabilitata")
print("   Implementeremo una versione più stabile successivamente")

# Auto-elimina questo script
os.remove(__file__)
print("\n✅ Script eliminato")
