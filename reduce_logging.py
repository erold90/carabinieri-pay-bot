#!/usr/bin/env python3
import subprocess

print("🔧 RIDUZIONE VERBOSITÀ LOG")
print("=" * 50)

# 1. Modifica main.py per ridurre il logging
print("\n📄 Aggiornamento configurazione logging in main.py...")

with open('main.py', 'r') as f:
    content = f.read()

# Trova la configurazione del logging
import re

# Pattern per trovare la configurazione logging
pattern = r'(logging\.basicConfig\([\s\S]*?\))'

def update_logging_config(match):
    config = match.group(0)
    
    # Cambia il livello a INFO invece di DEBUG
    config = re.sub(r'level=logging\.\w+', 'level=logging.INFO', config)
    
    return config

content = re.sub(pattern, update_logging_config, content)

# Riduci verbosità per moduli specifici
if "logging.getLogger('httpx').setLevel" in content:
    print("✅ Configurazione riduzione log già presente")
else:
    # Trova dove aggiungere dopo basicConfig
    insert_point = content.find("logger = logging.getLogger(__name__)")
    if insert_point > 0:
        insert_text = '''
# Riduci verbosità per moduli specifici
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('telegram.ext._application').setLevel(logging.WARNING)
logging.getLogger('telegram.ext.ExtBot').setLevel(logging.WARNING)
logging.getLogger('telegram.ext._updater').setLevel(logging.INFO)

'''
        content = content[:insert_point] + insert_text + content[insert_point:]
        print("✅ Aggiunta configurazione per ridurre verbosità moduli")

# Rimuovi o commenta i logger di debug non necessari
patterns_to_remove = [
    r'logger\.debug\(f"📨 Message update:.*?\n',
    r'logger\.debug\(f"🔘 Callback update:.*?\n',
    r'logger\.debug\(f"❓ Other update type:.*?\n',
    r'logger\.info\(f"📨 MESSAGGIO RICEVUTO:.*?\n'
]

for pattern in patterns_to_remove:
    content = re.sub(pattern, '# ' + pattern[:-2] + '\n', content)

# Mantieni solo i log importanti
content = content.replace(
    'logger.info(f"✅ COMANDO /start ricevuto',
    'logger.info(f"➡️ /start ricevuto'
)

# Salva main.py
with open('main.py', 'w') as f:
    f.write(content)

print("✅ Aggiornato main.py")

# 2. Crea un file di configurazione logging personalizzato
print("\n📄 Creazione configurazione logging personalizzata...")

logging_config = '''"""
Configurazione logging per CarabinieriPayBot
"""
import logging
import os

def setup_logging():
    """Configura il logging con livelli appropriati"""
    
    # Livello base: INFO in produzione, DEBUG in development
    level = logging.DEBUG if os.getenv('ENV') == 'development' else logging.INFO
    
    # Formato semplificato
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%H:%M:%S'  # Solo ora, senza data
    
    # Configurazione base
    logging.basicConfig(
        format=log_format,
        datefmt=date_format,
        level=level,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    
    # Silenzia moduli verbosi
    noisy_modules = [
        'httpx',
        'httpcore', 
        'telegram.ext.ExtBot',
        'telegram.ext._application',
        'telegram.ext._updater',
        'telegram.ext._basehandler',
        'telegram._bot',
        'telegram._request',
        'urllib3.connectionpool',
        'asyncio'
    ]
    
    for module in noisy_modules:
        logging.getLogger(module).setLevel(logging.WARNING)
    
    # Log solo errori per alcuni moduli
    error_only_modules = [
        'telegram.error',
        'telegram.ext._utils.webhookhandler'
    ]
    
    for module in error_only_modules:
        logging.getLogger(module).setLevel(logging.ERROR)
    
    # Il nostro logger principale resta a INFO
    app_logger = logging.getLogger('__main__')
    app_logger.setLevel(logging.INFO)
    
    return app_logger

# Funzione helper per log colorati (opzionale)
def log_info(message):
    """Log con emoji per maggiore chiarezza"""
    logger = logging.getLogger('__main__')
    logger.info(f"ℹ️  {message}")

def log_success(message):
    """Log successo"""
    logger = logging.getLogger('__main__')
    logger.info(f"✅ {message}")

def log_error(message):
    """Log errore"""
    logger = logging.getLogger('__main__')
    logger.error(f"❌ {message}")

def log_warning(message):
    """Log warning"""
    logger = logging.getLogger('__main__')
    logger.warning(f"⚠️  {message}")
'''

with open('utils/logging_config.py', 'w') as f:
    f.write(logging_config)

print("✅ Creato utils/logging_config.py")

# 3. Aggiorna main.py per usare la nuova configurazione
print("\n📄 Integrazione nuova configurazione in main.py...")

# Aggiungi import
if 'from utils.logging_config import setup_logging' not in content:
    # Trova dove aggiungere l'import
    import_point = content.find('import logging')
    if import_point > 0:
        end_of_line = content.find('\n', import_point)
        content = content[:end_of_line+1] + 'from utils.logging_config import setup_logging, log_info, log_success, log_error, log_warning\n' + content[end_of_line+1:]

# Sostituisci la configurazione logging
content = re.sub(
    r'# Enable logging[\s\S]*?logger = logging\.getLogger\(__name__\)',
    '''# Setup logging
logger = setup_logging()''',
    content
)

# Sostituisci alcuni logger.info con le nuove funzioni
replacements = [
    ('logger.info("🚀 Starting CarabinieriPayBot...")', 'log_info("Avvio CarabinieriPayBot...")'),
    ('logger.info("✅ Bot avviato e in ascolto!")', 'log_success("Bot avviato e in ascolto!")'),
    ('logger.error(f"❌ Errore', 'log_error(f"Errore'),
    ('logger.warning(f"⚠️', 'log_warning(f"'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Salva
with open('main.py', 'w') as f:
    f.write(content)

# 4. Aggiorna i principali handler per usare log più chiari
print("\n📄 Aggiornamento handler per log più chiari...")

handlers_to_update = [
    'handlers/service_handler.py',
    'handlers/start_handler.py'
]

for handler_file in handlers_to_update:
    try:
        with open(handler_file, 'r') as f:
            handler_content = f.read()
        
        # Rimuovi o commenta i log di debug eccessivi
        handler_content = re.sub(r'logger\.debug\(.*?\)', '# Removed debug log', handler_content)
        
        # Mantieni solo log importanti
        handler_content = handler_content.replace(
            'logger.info(f"User:',
            '# logger.debug(f"User:'
        )
        
        with open(handler_file, 'w') as f:
            f.write(handler_content)
        
        print(f"✅ Aggiornato {handler_file}")
    except Exception as e:
        print(f"⚠️  Errore aggiornando {handler_file}: {e}")

# 5. Test sintassi
print("\n🔍 Verifica sintassi...")

files_to_test = ['main.py', 'utils/logging_config.py']
all_ok = True

for file in files_to_test:
    try:
        with open(file, 'r') as f:
            compile(f.read(), file, 'exec')
        print(f"✅ {file} - OK")
    except SyntaxError as e:
        print(f"❌ {file} - Errore: {e}")
        all_ok = False

if all_ok:
    print("\n✅ Configurazione logging ottimizzata!")

# Mostra esempio di come appariranno i log
print("\n📋 ESEMPIO DEI NUOVI LOG:")
print("Prima:")
print("2025-05-31 17:59:35,986 - httpcore.http11 - DEBUG - receive_response_body.complete")
print("2025-05-31 17:59:35,987 - telegram.ext.ExtBot - DEBUG - Entering: edit_message_text")
print("\nDopo:")
print("17:59:35 - __main__ - INFO - ➡️ /start ricevuto da @username")
print("17:59:36 - __main__ - INFO - ✅ Servizio salvato con successo")
print("17:59:36 - __main__ - WARNING - ⚠️  Callback non gestito: unknown_callback")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: ridotta verbosità log per migliore leggibilità"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Logging ottimizzato!")
print("🔍 Ora vedrai solo:")
print("   - Comandi ricevuti")
print("   - Errori e warning importanti")
print("   - Operazioni completate con successo")
print("   - Callback non gestiti")
print("\n📵 NON vedrai più:")
print("   - Debug HTTP/HTTPS")
print("   - Dettagli interni di Telegram")
print("   - Log di ogni singolo update")

# Auto-elimina
import os
os.remove(__file__)
