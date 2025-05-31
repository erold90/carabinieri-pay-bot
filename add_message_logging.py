#!/usr/bin/env python3
import subprocess
import os

print("🔧 AGGIUNGO LOGGING MESSAGGI")
print("=" * 50)

# Aggiungi logging in start_handler.py
with open('handlers/start_handler.py', 'r') as f:
    content = f.read()

# Aggiungi import logging se manca
if 'import logging' not in content:
    lines = content.split('\n')
    # Trova dove inserire dopo gli altri import
    for i, line in enumerate(lines):
        if 'from' in line or 'import' in line:
            continue
        else:
            lines.insert(i, 'import logging')
            lines.insert(i+1, 'logger = logging.getLogger(__name__)')
            lines.insert(i+2, '')
            break
    content = '\n'.join(lines)

# Aggiungi log all'inizio di start_command
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'async def start_command(update: Update' in line:
        # Trova la prima riga di codice dopo la definizione
        j = i + 1
        # Salta docstring se presente
        if j < len(lines) and '"""' in lines[j]:
            while j < len(lines) and '"""' not in lines[j+1]:
                j += 1
            j += 2
        
        # Aggiungi logging
        if 'logger.info("START COMMAND CHIAMATO")' not in content:
            indent = '    '
            lines.insert(j, f'{indent}logger.info("🚀 START COMMAND CHIAMATO!")')
            lines.insert(j+1, f'{indent}logger.info(f"User: {{update.effective_user.id if update.effective_user else \'Unknown\'}}")')
            lines.insert(j+2, f'{indent}logger.info(f"Chat: {{update.effective_chat.id if update.effective_chat else \'Unknown\'}}")')
            print("✅ Aggiunto logging dettagliato in start_command")
        break

content = '\n'.join(lines)

# Salva
with open('handlers/start_handler.py', 'w') as f:
    f.write(content)

# Aggiungi anche un middleware di logging in main.py
print("\n📝 Aggiungo middleware di logging...")
with open('main.py', 'r') as f:
    main_content = f.read()

# Aggiungi funzione di logging se non esiste
if 'async def log_all_messages(' not in main_content:
    lines = main_content.split('\n')
    
    # Trova dove inserire (prima di main)
    for i, line in enumerate(lines):
        if 'def main():' in line:
            # Inserisci funzione prima di main
            log_function = '''
async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log tutti i messaggi per debug"""
    if update.message:
        logger.info(f"📨 MESSAGGIO RICEVUTO: '{update.message.text}' da @{update.message.from_user.username if update.message.from_user else 'Unknown'}")
        if update.message.text and update.message.text.startswith('/'):
            logger.info(f"   È UN COMANDO: {update.message.text}")
    elif update.callback_query:
        logger.info(f"🔘 CALLBACK RICEVUTO: '{update.callback_query.data}'")
'''
            lines.insert(i-1, log_function)
            break
    
    # Aggiungi handler come primo
    for i, line in enumerate(lines):
        if 'application.add_handler(CommandHandler("start"' in line:
            # Inserisci prima di start
            lines.insert(i, '    # Logger per debug - PRIMO handler')
            lines.insert(i+1, '    application.add_handler(MessageHandler(filters.ALL, log_all_messages), group=-10)')
            lines.insert(i+2, '    logger.info("📝 Message logger aggiunto")')
            lines.insert(i+3, '')
            print("✅ Aggiunto message logger come primo handler")
            break
    
    main_content = '\n'.join(lines)

# Salva main.py
with open('main.py', 'w') as f:
    f.write(main_content)

# Verifica sintassi
print("\n🔍 Verifica sintassi...")
for file in ['main.py', 'handlers/start_handler.py']:
    result = subprocess.run(['python3', '-m', 'py_compile', file], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {file} OK")
    else:
        print(f"❌ {file}: {result.stderr}")

# Commit e push
print("\n📤 Push logging...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "debug: aggiunto logging dettagliato per tracciare messaggi ricevuti"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ LOGGING AGGIUNTO!")
print("\nDopo il redeploy, quando invii /start dovresti vedere nei log:")
print("1. 📨 MESSAGGIO RICEVUTO: '/start' da @tuousername")
print("2. È UN COMANDO: /start")
print("3. 🚀 START COMMAND CHIAMATO!")
print("\nSe vedi solo 1 e 2, il problema è nel routing")
print("Se non vedi niente, il problema è nella connessione")

os.remove(__file__)
