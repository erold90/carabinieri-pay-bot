#!/usr/bin/env python3
import subprocess
import os

print("🔧 RIPRISTINO CLEAN CHAT E ANALISI PROFONDA")
print("=" * 50)

# 1. Ripristina clean_chat.py originale
print("\n1️⃣ Ripristino clean_chat.py...")
subprocess.run("git checkout utils/clean_chat.py", shell=True)
print("✅ Ripristinato")

# 2. Ripristina main.py 
print("\n2️⃣ Ripristino main.py per clean chat...")
subprocess.run("git checkout main.py", shell=True)
print("✅ Ripristinato")

# 3. Ripristina settings.py
print("\n3️⃣ Ripristino settings.py...")
subprocess.run("git checkout config/settings.py", shell=True)
print("✅ Ripristinato")

# 4. Ora analizziamo perché /start non funziona
print("\n" + "=" * 50)
print("🔍 ANALISI PROFONDA DEL PROBLEMA")

# Verifica handler registration
print("\n📌 Verifica registrazione handler in main.py:")
with open('main.py', 'r') as f:
    main_content = f.read()
    
# Cerca CommandHandler per start
if 'CommandHandler("start", start_command)' in main_content:
    print("✅ Handler /start registrato correttamente")
else:
    print("❌ Handler /start NON trovato!")

# Verifica import di start_command
if 'from handlers.start_handler import start_command' in main_content:
    print("✅ start_command importato correttamente")
else:
    print("❌ start_command NON importato!")

# Verifica ordine degli handler
print("\n📌 Ordine degli handler:")
lines = main_content.split('\n')
handler_order = []
for i, line in enumerate(lines):
    if 'application.add_handler(' in line:
        handler_order.append(f"Linea {i+1}: {line.strip()}")

for h in handler_order[:10]:  # Primi 10 handler
    print(f"  {h}")

# 5. Aggiungi logging PRIMA di tutti gli handler
print("\n" + "=" * 50)
print("📝 Aggiungo logging di debug SEMPLICE...")

with open('main.py', 'r') as f:
    content = f.read()

# Aggiungi handler di log come PRIMO handler
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'application = Application.builder()' in line:
        # Trova dove iniziano gli handler
        j = i
        while j < len(lines) and 'application.add_handler' not in lines[j]:
            j += 1
        
        if j < len(lines):
            # Inserisci PRIMA di tutti gli altri handler
            debug_code = '''
    # DEBUG: Log TUTTI gli update ricevuti
    async def debug_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            logger.info(f"[DEBUG] Messaggio ricevuto: {update.message.text} da {update.effective_user.id}")
        elif update.callback_query:
            logger.info(f"[DEBUG] Callback ricevuto: {update.callback_query.data}")
        # NON blocca il messaggio, lascia che continui
    
    application.add_handler(MessageHandler(filters.ALL, debug_log), group=-100)
    logger.info("Debug handler registrato")
    '''
            lines.insert(j, debug_code)
            print("✅ Aggiunto debug handler come PRIMO")
            break

content = '\n'.join(lines)

# 6. Verifica che start_command esista e funzioni
print("\n📌 Verifica start_command in start_handler.py:")
with open('handlers/start_handler.py', 'r') as f:
    start_content = f.read()
    
if 'async def start_command(update: Update' in start_content:
    print("✅ Funzione start_command trovata")
    
    # Aggiungi log all'INIZIO della funzione
    lines = start_content.split('\n')
    for i, line in enumerate(lines):
        if 'async def start_command(update: Update' in line:
            # Trova la prima riga di codice (dopo docstring)
            j = i + 1
            while j < len(lines) and (lines[j].strip() == '' or '"""' in lines[j]):
                j += 1
            
            # Inserisci log
            indent = '    '
            lines.insert(j, f'{indent}logger.info("[START] Comando /start ricevuto!")')
            lines.insert(j+1, f'{indent}logger.info(f"[START] User: {{update.effective_user.id if update.effective_user else \'Unknown\'}}")')
            print("✅ Aggiunto logging in start_command")
            break
    
    # Aggiungi logger se manca
    if 'logger = logging.getLogger(__name__)' not in start_content:
        # Aggiungi dopo gli import
        for i, line in enumerate(lines):
            if 'from' not in line and 'import' not in line and line.strip() != '':
                lines.insert(i, 'import logging')
                lines.insert(i+1, 'logger = logging.getLogger(__name__)')
                lines.insert(i+2, '')
                break
    
    start_content = '\n'.join(lines)
    
    with open('handlers/start_handler.py', 'w') as f:
        f.write(start_content)

# Salva main.py
with open('main.py', 'w') as f:
    f.write(content)

# 7. Disabilita TEMPORANEAMENTE il middleware di pulizia
print("\n📌 Disabilito TEMPORANEAMENTE cleanup_middleware...")
with open('main.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'MessageHandler(filters.ALL, cleanup_middleware)' in line:
        lines[i] = '    # TEMP DISABLED: ' + line.lstrip()
        print("✅ cleanup_middleware temporaneamente disabilitato")

with open('main.py', 'w') as f:
    f.writelines(lines)

# Verifica sintassi
print("\n🔍 Verifica sintassi...")
for file in ['main.py', 'handlers/start_handler.py']:
    result = subprocess.run(['python3', '-m', 'py_compile', file], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {file} OK")
    else:
        print(f"❌ {file}: {result.stderr}")

# Commit
print("\n📤 Push modifiche di debug...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "debug: ripristinato clean chat e aggiunto logging dettagliato per diagnosticare /start"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ FATTO!")
print("\n🔍 Ora quando invii /start dovresti vedere nei log:")
print("1. [DEBUG] Messaggio ricevuto: /start da USER_ID")
print("2. [START] Comando /start ricevuto!")
print("3. [START] User: USER_ID")
print("\nSe vedi solo il primo, il problema è negli handler.")
print("Se non vedi niente, il problema è nella connessione Telegram.")

os.remove(__file__)
