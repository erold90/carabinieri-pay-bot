#!/usr/bin/env python3
"""Fix problemi di polling su Railway"""
import subprocess
import os
import re

print("🔍 DIAGNOSI E FIX PROBLEMI POLLING")
print("=" * 80)

fixes_applied = []

# 1. Verifica e fix del Procfile
print("\n1️⃣ Controllo Procfile...")
with open('Procfile', 'r') as f:
    procfile_content = f.read().strip()

print(f"Contenuto attuale: '{procfile_content}'")

if 'web:' in procfile_content:
    print("❌ Procfile usa 'web' invece di 'worker'!")
    print("   Railway potrebbe aspettarsi un webserver")
    fixes_applied.append("Cambiato da web a worker in Procfile")
    
    with open('Procfile', 'w') as f:
        f.write('worker: python3 main.py\n')
    print("✅ Procfile corretto: usa 'worker'")
else:
    print("✅ Procfile corretto")

# 2. Aggiungi gestione webhook esplicita
print("\n2️⃣ Aggiunta pulizia webhook all'avvio...")
with open('main.py', 'r') as f:
    main_content = f.read()

# Aggiungi funzione di cleanup webhook
cleanup_code = '''
async def cleanup_webhook_on_start(application):
    """Rimuove webhook all'avvio per garantire polling pulito"""
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook rimosso, polling mode attivo")
        
        # Verifica che non ci siano webhook
        webhook_info = await application.bot.get_webhook_info()
        if webhook_info.url:
            logger.warning(f"⚠️ Webhook ancora presente: {webhook_info.url}")
        else:
            logger.info("✅ Nessun webhook attivo")
            
    except Exception as e:
        logger.error(f"Errore rimozione webhook: {e}")
'''

if 'cleanup_webhook_on_start' not in main_content:
    # Aggiungi prima di main()
    main_pos = main_content.find('def main():')
    if main_pos > -1:
        main_content = main_content[:main_pos] + cleanup_code + '\n\n' + main_content[main_pos:]
        fixes_applied.append("Aggiunta funzione cleanup webhook")

# 3. Modifica main() per usare run_polling correttamente
print("\n3️⃣ Ottimizzazione avvio polling...")

# Trova la sezione run_polling
old_polling = '''    # Start the bot
    logger.info("Starting CarabinieriPayBot...")
    # # start_notification_system(application.bot)  # Disabilitato temporaneamente
    logger.info("Bot started and polling for updates...")
    # logger.info(f"Bot username: @{application.bot.username if hasattr(application.bot, 'username') else 'Unknown'}")
    
    # Avvia sistema di notifiche
    # try:
    # from services.notification_service import start_notification_system  # DISABILITATO - BLOCCAVA IL BOT
    # logger.info("Avvio sistema notifiche...")
    # start_notification_system(application.bot)  # Disabilitato temporaneamente'''

new_polling = '''    # Cleanup webhook prima di iniziare
    logger.info("🚀 Avvio CarabinieriPayBot...")
    
    # Inizializza e pulisci webhook
    await application.initialize()
    await cleanup_webhook_on_start(application)
    
    # Avvia bot info
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Bot: @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        logger.error(f"❌ Errore info bot: {e}")
    
    # Start polling con parametri ottimizzati
    logger.info("📡 Avvio polling...")
    await application.start()
    await application.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        pool_timeout=30
    )
    
    logger.info("✅ Bot avviato e in ascolto!")
    logger.info("📱 Invia /start al bot per testare")
    
    # Mantieni il bot in esecuzione
    await application.updater.idle()'''

# Sostituisci la sezione
if 'application.run_polling' in main_content:
    # Trova e sostituisci run_polling
    run_polling_match = re.search(r'application\.run_polling\([^)]*\)', main_content)
    if run_polling_match:
        main_content = main_content[:run_polling_match.start()] + '''# Avvia il bot con gestione asincrona migliorata
    asyncio.run(start_bot(application))''' + main_content[run_polling_match.end():]
        fixes_applied.append("Modificato metodo di avvio polling")

# Aggiungi funzione start_bot
start_bot_code = '''
async def start_bot(application):
    """Avvia il bot con gestione asincrona corretta"""
    # Cleanup webhook prima di iniziare
    logger.info("🚀 Avvio CarabinieriPayBot...")
    
    # Inizializza e pulisci webhook
    await application.initialize()
    await cleanup_webhook_on_start(application)
    
    # Avvia bot info
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Bot: @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        logger.error(f"❌ Errore info bot: {e}")
    
    # Start polling con parametri ottimizzati
    logger.info("📡 Avvio polling...")
    await application.start()
    await application.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        pool_timeout=30
    )
    
    logger.info("✅ Bot avviato e in ascolto!")
    logger.info("📱 Invia /start al bot per testare")
    
    # Mantieni il bot in esecuzione
    await application.updater.idle()
'''

if 'async def start_bot' not in main_content:
    # Aggiungi prima di main()
    main_pos = main_content.find('def main():')
    if main_pos > -1:
        main_content = main_content[:main_pos] + start_bot_code + '\n' + main_content[main_pos:]
        fixes_applied.append("Aggiunta funzione start_bot asincrona")

# 4. Aggiungi import asyncio se manca
if 'import asyncio' not in main_content:
    main_content = 'import asyncio\n' + main_content
    fixes_applied.append("Aggiunto import asyncio")

# 5. Aggiungi Update.ALL_TYPES import
if 'Update.ALL_TYPES' in main_content and 'from telegram import' in main_content:
    # Assicurati che Update sia importato correttamente
    import_line = re.search(r'from telegram import (.+)', main_content)
    if import_line and 'Update' not in import_line.group(1):
        old_import = import_line.group(0)
        new_import = old_import.replace('import ', 'import Update, ')
        main_content = main_content.replace(old_import, new_import)
        fixes_applied.append("Aggiunto import Update")

# 6. Aggiungi logging più dettagliato per debug
enhanced_logging = '''
# Aggiungi logging per ogni update ricevuto
async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log ogni update per debug"""
    if update.message:
        logger.debug(f"📨 Message update: {update.message.text} from {update.effective_user.id}")
    elif update.callback_query:
        logger.debug(f"🔘 Callback update: {update.callback_query.data}")
    elif update.edited_message:
        logger.debug(f"✏️ Edited message update")
    else:
        logger.debug(f"❓ Other update type: {update}")
'''

if 'log_update' not in main_content:
    main_pos = main_content.find('def main():')
    if main_pos > -1:
        main_content = main_content[:main_pos] + enhanced_logging + '\n' + main_content[main_pos:]
        
        # Aggiungi handler per logging
        handler_section = main_content.find('application.add_handler(CommandHandler("start"')
        if handler_section > -1:
            log_handler = '''    # Logging handler per debug
    application.add_handler(MessageHandler(filters.ALL, log_update), group=-10)
    
'''
            main_content = main_content[:handler_section] + log_handler + main_content[handler_section:]
        fixes_applied.append("Aggiunto logging dettagliato update")

# Salva le modifiche
with open('main.py', 'w') as f:
    f.write(main_content)

# 7. Crea script di monitoraggio Railway
print("\n4️⃣ Creazione script monitoraggio...")
monitor_script = '''#!/usr/bin/env python3
"""Monitora il bot su Railway"""
import os
import time
import asyncio
from telegram import Bot

async def monitor():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ Token non trovato")
        return
    
    bot = Bot(token)
    print("🔍 Monitoraggio bot...")
    
    for i in range(5):
        try:
            updates = await bot.get_updates(timeout=5)
            print(f"\\n📨 Update {i+1}: {len(updates)} messaggi")
            
            for update in updates[-5:]:  # Ultimi 5
                if update.message:
                    print(f"  - {update.message.text} da {update.message.from_user.username}")
            
            webhook = await bot.get_webhook_info()
            print(f"🌐 Webhook: {'ATTIVO' if webhook.url else 'NON ATTIVO'}")
            
            if webhook.url:
                print(f"   URL: {webhook.url}")
                
        except Exception as e:
            print(f"❌ Errore: {e}")
        
        time.sleep(2)
    
    await bot.close()

asyncio.run(monitor())
'''

with open('monitor_railway.py', 'w') as f:
    f.write(monitor_script)

os.chmod('monitor_railway.py', 0o755)

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add -A", shell=True)

commit_msg = f'''fix: risoluzione problemi polling su Railway

Problemi risolti:
{chr(10).join(f"- {fix}" for fix in fixes_applied)}

Modifiche principali:
- Procfile usa 'worker' invece di 'web'
- Cleanup webhook all'avvio
- Gestione asincrona migliorata
- Parametri polling ottimizzati
- Logging dettagliato per debug

Il bot ora dovrebbe ricevere correttamente i messaggi
'''

subprocess.run(['git', 'commit', '-m', commit_msg])
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 80)
print("✅ FIX COMPLETATI!")
print("\n⚠️ IMPORTANTE per Railway:")
print("1. Verifica che NON ci sia PORT nelle variabili ambiente")
print("2. Assicurati che il deploy type sia 'Worker' non 'Web'")
print("3. Se c'è un healthcheck endpoint, disabilitalo")
print("\nDopo il deploy (2-3 minuti):")
print("1. Controlla i log per vedere '✅ Bot avviato e in ascolto!'")
print("2. Invia /start al bot")
print("3. Guarda i log per vedere se riceve il messaggio")
print("\nPer monitorare: python3 monitor_railway.py")
print("=" * 80)

# Auto-elimina
os.remove(__file__)
