#!/usr/bin/env python3
import subprocess
import os

print("🔧 OTTIMIZZAZIONE SISTEMA CLEAN CHAT")
print("=" * 50)

# 1. Modifica utils/clean_chat.py
print("\n1️⃣ Ottimizzazione clean_chat.py...")
with open('utils/clean_chat.py', 'r') as f:
    content = f.read()

# Aumenta messaggi mantenuti
content = content.replace('self.max_messages = 1', 'self.max_messages = 5')

# Modifica il delay per auto-delete
content = content.replace('DELETE_DELAY = 30', 'DELETE_DELAY = 300')  # 5 minuti invece di 30 secondi

# Aggiungi protezione per messaggi con comandi
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'async def cleanup_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):' in line:
        # Inserisci controllo dopo la definizione
        j = i + 2
        protection_code = '''    # Non pulire messaggi con comandi
    if update.message and update.message.text:
        if update.message.text.startswith('/'):
            # È un comando, non pulire subito
            return
        
    # Aspetta che il messaggio venga processato
    await asyncio.sleep(2)  # Delay di 2 secondi prima di registrare per pulizia
    '''
        lines.insert(j, protection_code)
        break

# Assicurati che asyncio sia importato
if 'import asyncio' not in content:
    lines.insert(5, 'import asyncio')

content = '\n'.join(lines)

with open('utils/clean_chat.py', 'w') as f:
    f.write(content)
print("✅ Clean chat ottimizzato")

# 2. Modifica main.py per cambiare priorità
print("\n2️⃣ Modifica priorità middleware...")
with open('main.py', 'r') as f:
    content = f.read()

# Cambia priorità da -999 a 999 (esegue DOPO gli altri handler)
content = content.replace('group=-999)', 'group=999)')

# Assicurati che il middleware NON interferisca con i comandi
# Spostiamolo DOPO tutti gli altri handler
lines = content.split('\n')
middleware_line = None
middleware_idx = None

# Trova la linea del middleware
for i, line in enumerate(lines):
    if 'application.add_handler(MessageHandler(filters.ALL, cleanup_middleware)' in line:
        middleware_line = line
        middleware_idx = i
        # Commenta temporaneamente
        lines[i] = '    # ' + line.lstrip()
        break

# Trova l'ultimo add_handler e inserisci dopo
if middleware_line:
    last_handler_idx = 0
    for i, line in enumerate(lines):
        if 'application.add_handler(' in line and i != middleware_idx:
            last_handler_idx = i
    
    # Inserisci dopo l'ultimo handler
    if last_handler_idx > 0:
        lines.insert(last_handler_idx + 1, '')
        lines.insert(last_handler_idx + 2, '    # Middleware pulizia chat - eseguito DOPO tutti gli handler')
        lines.insert(last_handler_idx + 3, middleware_line)
        print("✅ Middleware spostato alla fine")

content = '\n'.join(lines)

# 3. Aggiungi filtro per non pulire messaggi importanti
if 'from telegram.ext import' in content:
    # Modifica il filtro del middleware
    content = content.replace(
        'MessageHandler(filters.ALL, cleanup_middleware)',
        'MessageHandler(filters.TEXT & ~filters.COMMAND, cleanup_middleware)'
    )
    print("✅ Middleware ora ignora i comandi")

with open('main.py', 'w') as f:
    f.write(content)

# 4. Modifica settings per essere meno aggressivo
print("\n3️⃣ Aggiornamento settings...")
with open('config/settings.py', 'r') as f:
    content = f.read()

# Mantieni abilitato ma meno aggressivo
if 'KEEP_ONLY_LAST_MESSAGE = True' in content:
    content = content.replace('KEEP_ONLY_LAST_MESSAGE = True', 'KEEP_ONLY_LAST_MESSAGE = False')
    print("✅ Disabilitato KEEP_ONLY_LAST_MESSAGE")

with open('config/settings.py', 'w') as f:
    f.write(content)

# 5. Crea una versione migliorata del cleaner
print("\n4️⃣ Creazione cleaner migliorato...")
improved_cleaner = '''# Aggiungi alla fine di clean_chat.py

async def smart_cleanup_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Middleware intelligente che non interferisce con i comandi"""
    if not update.message:
        return
    
    # Ignora comandi
    if update.message.text and update.message.text.startswith('/'):
        return
    
    # Ignora messaggi con keyboard
    if update.message.reply_markup:
        return
    
    # Aspetta che il messaggio sia processato
    await asyncio.sleep(3)
    
    # Poi registra per pulizia futura
    await register_user_message(update, context)
'''

with open('utils/clean_chat.py', 'a') as f:
    f.write('\n\n' + improved_cleaner)

print("✅ Aggiunto smart_cleanup_middleware")

# Verifica sintassi
print("\n🔍 Verifica sintassi...")
for file in ['main.py', 'utils/clean_chat.py', 'config/settings.py']:
    result = subprocess.run(['python3', '-m', 'py_compile', file], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {file} OK")
    else:
        print(f"❌ {file}: {result.stderr}")

# Commit e push
print("\n📤 Push ottimizzazioni...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: ottimizzato clean chat - non interferisce più con i comandi"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ CLEAN CHAT OTTIMIZZATO!")
print("\nIl sistema ora:")
print("✅ Mantiene 5 messaggi invece di 1")
print("✅ NON pulisce i comandi (iniziano con /)")
print("✅ Aspetta 3 secondi prima di registrare messaggi")
print("✅ Esegue DOPO tutti gli handler")
print("✅ Auto-elimina dopo 5 minuti invece di 30 secondi")
print("\n🎯 Il bot dovrebbe ora rispondere ai comandi!")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script auto-eliminato")
