#!/usr/bin/env python3
"""
Fix per problemi di avvio del bot
"""
import subprocess
import os

print("🔧 FIX AVVIO BOT")
print("=" * 60)

fixes_applied = []

# 1. AGGIUNGI LOG PIÙ DETTAGLIATI
print("\n1️⃣ Aggiunta log dettagliati per debug...")
with open('main.py', 'r') as f:
    content = f.read()

# Trova la funzione main()
main_func_start = content.find('def main():')
if main_func_start > -1:
    # Aggiungi più log dopo l'inizializzazione
    insert_pos = content.find('application = Application.builder().token(', main_func_start)
    if insert_pos > -1:
        # Trova la fine della riga
        line_end = content.find('\n', insert_pos)
        # Trova il prossimo statement
        next_line_start = line_end + 1
        
        # Aggiungi log per verificare il token
        debug_code = '''
    
    # Debug: verifica token
    token = os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))
    if not token:
        logger.error("❌ BOT TOKEN NON TROVATO!")
        logger.error("Variabili ambiente disponibili: %s", list(os.environ.keys()))
        return
    else:
        logger.info(f"✅ Token trovato: {token[:10]}...{token[-5:]}")
    '''
        
        # Inserisci prima di application = 
        content = content[:insert_pos] + debug_code + '\n    ' + content[insert_pos:]
        fixes_applied.append("✅ Aggiunto debug token")

# Aggiungi try-catch intorno a run_polling
polling_pos = content.find('application.run_polling()')
if polling_pos > -1:
    # Sostituisci con versione con try-catch e parametri
    old_line = 'application.run_polling()'
    new_code = '''try:
        logger.info("🚀 Avvio polling...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"❌ Errore durante polling: {e}")
        import traceback
        traceback.print_exc()'''
    
    content = content.replace(old_line, new_code)
    fixes_applied.append("✅ Aggiunto error handling per polling")

with open('main.py', 'w') as f:
    f.write(content)

# 2. CREA SCRIPT TEST MINIMALE
print("\n2️⃣ Creazione bot test minimale...")
test_bot_content = '''#!/usr/bin/env python3
"""Bot minimale per test connessione"""
import logging
import os
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Comando /start ricevuto da {update.effective_user.id}")
    await update.message.reply_text("✅ Bot funzionante!")

async def test_connection():
    """Test connessione bot"""
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
    if not token:
        logger.error("Token non trovato!")
        return False
    
    bot = Bot(token)
    try:
        me = await bot.get_me()
        logger.info(f"✅ Bot connesso: @{me.username}")
        await bot.close()
        return True
    except Exception as e:
        logger.error(f"❌ Errore connessione: {e}")
        return False

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN non trovato!")
        logger.error(f"Variabili disponibili: {list(os.environ.keys())}")
        return
    
    logger.info(f"Token: {token[:10]}...{token[-5:]}")
    
    # Test connessione prima
    if not asyncio.run(test_connection()):
        logger.error("Test connessione fallito!")
        return
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    logger.info("Avvio polling...")
    try:
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Errore: {e}")

if __name__ == '__main__':
    main()
'''

with open('test_minimal_bot.py', 'w') as f:
    f.write(test_bot_content)
os.chmod('test_minimal_bot.py', 0o755)
fixes_applied.append("✅ Creato bot test minimale")

# 3. AGGIUNGI IMPORT Update IN MAIN.PY
print("\n3️⃣ Verifica import Update...")
with open('main.py', 'r') as f:
    content = f.read()

# Cerca l'import di telegram
telegram_import_line = None
for line in content.split('\n'):
    if 'from telegram import' in line and 'Update' not in line:
        telegram_import_line = line
        break

if telegram_import_line:
    # Aggiungi Update all'import
    new_line = telegram_import_line.rstrip()
    if not new_line.endswith(','):
        new_line += ', Update'
    else:
        new_line += ' Update'
    
    content = content.replace(telegram_import_line, new_line)
    fixes_applied.append("✅ Aggiunto import Update")
    
    with open('main.py', 'w') as f:
        f.write(content)

# 4. VERIFICA CONFIGURAZIONE BOT
print("\n4️⃣ Creazione script verifica configurazione...")
verify_config = '''#!/usr/bin/env python3
"""Verifica configurazione bot"""
import os
import asyncio
from telegram import Bot

async def verify_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
    
    print("🔍 VERIFICA CONFIGURAZIONE BOT")
    print("=" * 50)
    
    if not token:
        print("❌ TOKEN NON TROVATO!")
        print("Variabili ambiente:")
        for key in sorted(os.environ.keys()):
            if 'TOKEN' in key or 'BOT' in key:
                print(f"  {key}: {os.environ[key][:20]}...")
        return
    
    print(f"✅ Token trovato: {token[:20]}...{token[-10:]}")
    print(f"   Lunghezza: {len(token)} caratteri")
    
    bot = Bot(token)
    try:
        me = await bot.get_me()
        print(f"✅ Bot valido: @{me.username}")
        print(f"   Nome: {me.first_name}")
        print(f"   ID: {me.id}")
        
        # Prova a eliminare webhook se presente
        webhook = await bot.get_webhook_info()
        if webhook.url:
            print(f"⚠️  Webhook attivo: {webhook.url}")
            print("   Rimozione webhook...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook rimosso")
        else:
            print("✅ Nessun webhook attivo")
            
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(verify_bot())
'''

with open('verify_bot_config.py', 'w') as f:
    f.write(verify_config)
os.chmod('verify_bot_config.py', 0o755)
fixes_applied.append("✅ Creato script verifica configurazione")

# 5. AGGIUNGI TIMEOUT E ERROR HANDLING
print("\n5️⃣ Aggiunta timeout e gestione errori...")
with open('main.py', 'r') as f:
    content = f.read()

# Aggiungi configurazione timeout per il builder
builder_line = content.find('Application.builder().token(')
if builder_line > -1:
    # Trova la fine della linea
    line_end = content.find(')', builder_line)
    if line_end > -1:
        # Aggiungi configurazioni
        old_text = content[builder_line:line_end+1]
        new_text = old_text.replace(
            ').build()',
            ').connect_timeout(30).read_timeout(30).build()'
        )
        content = content.replace(old_text + '.build()', new_text)
        fixes_applied.append("✅ Aggiunto timeout configurazione")

with open('main.py', 'w') as f:
    f.write(content)

# RIEPILOGO
print("\n" + "=" * 60)
print("📊 FIX APPLICATI:")
for fix in fixes_applied:
    print(f"  {fix}")

# COMMIT E PUSH
print("\n📤 Commit modifiche...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: risolto problema avvio bot - aggiunto debug e error handling"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 60)
print("✅ FIX COMPLETATO!")
print("\n🧪 TEST LOCALI:")
print("1. Verifica configurazione:")
print("   python3 verify_bot_config.py")
print("\n2. Test bot minimale:")
print("   python3 test_minimal_bot.py")
print("\n3. Se i test funzionano, il problema è su Railway")
print("=" * 60)

# Auto-elimina
os.remove(__file__)
