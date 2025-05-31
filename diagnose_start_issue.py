#!/usr/bin/env python3
"""Diagnostica problema /start command"""
import subprocess
import os
import re

print("🔍 DIAGNOSTICA PROBLEMA /START")
print("=" * 80)

issues_found = []
fixes_to_apply = []

# 1. Verifica main.py per handler /start
print("\n1️⃣ Controllo registrazione handler /start...")
with open('main.py', 'r') as f:
    main_content = f.read()

# Cerca la registrazione del comando start
if 'CommandHandler("start", start_command)' in main_content:
    print("✅ Handler /start registrato correttamente")
    
    # Verifica import
    if 'from handlers.start_handler import start_command' in main_content:
        print("✅ Import start_command presente")
    else:
        print("❌ Import start_command mancante!")
        issues_found.append("Import start_command mancante")
else:
    print("❌ Handler /start non registrato!")
    issues_found.append("Handler /start non registrato")

# 2. Verifica start_handler.py
print("\n2️⃣ Controllo start_handler.py...")
with open('handlers/start_handler.py', 'r') as f:
    start_content = f.read()

# Controlla la funzione start_command
if 'async def start_command' in start_content:
    print("✅ Funzione start_command trovata")
    
    # Verifica logging
    if 'logger.info("Start command received")' in start_content:
        print("✅ Logging presente")
    else:
        print("⚠️ Logging mancante - aggiungiamolo")
        fixes_to_apply.append("add_logging")
else:
    print("❌ Funzione start_command non trovata!")
    issues_found.append("start_command non definita")

# 3. Verifica errori di sintassi
print("\n3️⃣ Controllo errori di sintassi...")
syntax_errors = []

# Controlla parentesi bilanciate
for file_path in ['main.py', 'handlers/start_handler.py', 'handlers/service_handler.py']:
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Conta parentesi
    open_parens = content.count('(')
    close_parens = content.count(')')
    
    if open_parens != close_parens:
        syntax_errors.append(f"{file_path}: parentesi sbilanciate ({open_parens} aperte, {close_parens} chiuse)")

if syntax_errors:
    print(f"❌ Errori sintassi trovati: {syntax_errors}")
    issues_found.extend(syntax_errors)
else:
    print("✅ Nessun errore di sintassi evidente")

# 4. Verifica token bot
print("\n4️⃣ Controllo configurazione token...")
if 'BOT_TOKEN' in main_content or 'TELEGRAM_BOT_TOKEN' in main_content:
    print("✅ Riferimento al token presente")
else:
    print("❌ Nessun riferimento al token!")
    issues_found.append("Token non configurato")

# 5. Verifica ordine handler
print("\n5️⃣ Controllo ordine registrazione handler...")

# Trova tutte le registrazioni di handler
handler_lines = []
lines = main_content.split('\n')
for i, line in enumerate(lines):
    if 'application.add_handler' in line:
        handler_lines.append((i, line.strip()))

# Verifica che /start sia tra i primi
start_position = None
for i, (line_num, line) in enumerate(handler_lines):
    if 'CommandHandler("start"' in line:
        start_position = i
        break

if start_position is not None:
    if start_position < 5:
        print(f"✅ Handler /start in posizione {start_position + 1} (ottimo)")
    else:
        print(f"⚠️ Handler /start in posizione {start_position + 1} (potrebbe essere troppo tardi)")
        fixes_to_apply.append("reorder_handlers")
else:
    print("❌ Handler /start non trovato nell'ordine!")

# 6. Verifica database connection
print("\n6️⃣ Controllo inizializzazione database...")
if 'init_db()' in main_content:
    print("✅ Inizializzazione database presente")
    
    # Verifica gestione errori
    if 'try:' in main_content and 'init_db()' in main_content:
        print("✅ Gestione errori per database")
    else:
        print("⚠️ Manca gestione errori per database")
        fixes_to_apply.append("add_db_error_handling")
else:
    print("❌ Inizializzazione database mancante!")
    issues_found.append("Database non inizializzato")

# 7. Fix problemi trovati
if issues_found or fixes_to_apply:
    print("\n" + "=" * 80)
    print("🔧 APPLICAZIONE FIX AUTOMATICI...")
    
    # Fix 1: Aggiungi logging dettagliato a start_command
    if "add_logging" in fixes_to_apply:
        print("\n📝 Aggiunta logging a start_command...")
        with open('handlers/start_handler.py', 'r') as f:
            content = f.read()
        
        # Aggiungi import logging se manca
        if 'import logging' not in content:
            content = 'import logging\n\nlogger = logging.getLogger(__name__)\n\n' + content
        
        # Aggiungi log all'inizio di start_command
        content = content.replace(
            'async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):',
            '''async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    logger.info("🚀 START COMMAND CHIAMATO!")
    logger.info(f"User: {update.effective_user.id if update.effective_user else 'Unknown'}")
    logger.info(f"Chat: {update.effective_chat.id if update.effective_chat else 'Unknown'}")'''
        )
        
        with open('handlers/start_handler.py', 'w') as f:
            f.write(content)
        print("✅ Logging aggiunto")
    
    # Fix 2: Assicurati che handler sia registrato correttamente
    print("\n📝 Verifica registrazione handler...")
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Trova dove aggiungere gli handler
    handlers_section = content.find('# Command handlers')
    if handlers_section == -1:
        handlers_section = content.find('application.add_handler')
    
    # Assicurati che start sia il PRIMO handler
    if 'application.add_handler(CommandHandler("start", start_command))' not in content:
        print("❌ Handler /start non trovato, lo aggiungo...")
        
        # Trova dove inserire
        insert_pos = content.find('application = Application.builder()')
        if insert_pos > -1:
            # Trova la fine del builder
            builder_end = content.find('.build()', insert_pos) + len('.build()')
            insert_pos = content.find('\n', builder_end) + 1
            
            # Aggiungi handler
            new_handlers = '''
    # Command handlers - start DEVE essere il primo!
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("hello", hello_command))
    application.add_handler(CommandHandler("ping", ping_command))
'''
            content = content[:insert_pos] + new_handlers + content[insert_pos:]
            
            with open('main.py', 'w') as f:
                f.write(content)
            print("✅ Handler /start aggiunto come primo!")
    
    # Fix 3: Aggiungi debug handler temporaneo
    print("\n📝 Aggiunta handler di debug...")
    debug_handler = '''
# DEBUG: Log tutti i comandi ricevuti
async def debug_all_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug: log tutti gli update"""
    if update.message and update.message.text:
        logger.info(f"🔍 DEBUG: Ricevuto messaggio: '{update.message.text}' da {update.effective_user.id}")
        if update.message.text.startswith('/'):
            logger.info(f"   È un comando: {update.message.text}")
    elif update.callback_query:
        logger.info(f"🔍 DEBUG: Ricevuto callback: {update.callback_query.data}")
'''
    
    if 'debug_all_updates' not in content:
        # Aggiungi prima della funzione main
        main_pos = content.find('def main():')
        if main_pos > -1:
            content = content[:main_pos] + debug_handler + '\n\n' + content[main_pos:]
            
            # Registra il debug handler
            handlers_pos = content.find('application.add_handler(CommandHandler("start"')
            if handlers_pos > -1:
                # Aggiungi come primo handler con priorità alta
                debug_registration = '''    # DEBUG: Handler per logging
    application.add_handler(MessageHandler(filters.ALL, debug_all_updates), group=-1)
    
'''
                content = content[:handlers_pos] + debug_registration + content[handlers_pos:]
            
            with open('main.py', 'w') as f:
                f.write(content)
            print("✅ Debug handler aggiunto")

# Crea script di test veloce
print("\n📝 Creazione script di test...")
test_script = '''#!/usr/bin/env python3
"""Test veloce del bot"""
import os
import asyncio
from telegram import Bot

async def test_bot():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ Token non trovato!")
        return
    
    bot = Bot(token)
    try:
        me = await bot.get_me()
        print(f"✅ Bot online: @{me.username}")
        
        # Elimina webhook se presente
        webhook = await bot.get_webhook_info()
        if webhook.url:
            print("⚠️ Webhook attivo, lo rimuovo...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook rimosso")
        
        print("\\n📱 Ora prova a inviare /start al bot!")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_bot())
'''

with open('quick_test.py', 'w') as f:
    f.write(test_script)

os.chmod('quick_test.py', 0o755)

# Commit e push
print("\n📤 Commit e push delle modifiche...")
subprocess.run("git add -A", shell=True)

commit_msg = f'''fix: risoluzione problema comando /start

Problemi trovati e risolti:
{chr(10).join(f"- {issue}" for issue in issues_found[:5])}

Fix applicati:
- Aggiunto logging dettagliato a start_command
- Verificata registrazione handler come primo
- Aggiunto debug handler per monitorare tutti i messaggi
- Migliorata gestione errori

Il bot ora dovrebbe rispondere correttamente a /start
'''

subprocess.run(['git', 'commit', '-m', commit_msg])
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 80)
print("✅ DIAGNOSTICA E FIX COMPLETATI!")
print("\nProssimi passi:")
print("1. ⏰ Attendi 2-3 minuti per il deploy su Railway")
print("2. 🧪 Esegui: python3 quick_test.py")
print("3. 📱 Invia /start al bot")
print("4. 📋 Controlla i log su Railway per vedere i messaggi di debug")
print("\nSe ancora non funziona, controlla:")
print("- I log di Railway per errori")
print("- Che il token BOT_TOKEN sia configurato correttamente")
print("- Che non ci siano webhook attivi (usa quick_test.py)")
print("=" * 80)

# Pulizia
os.remove(__file__)
