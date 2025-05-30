from telegram.ext import ContextTypes
from telegram import Update
#!/usr/bin/env python3
import subprocess

print("🔧 Fix tutti i callback delle impostazioni")
print("=" * 50)

# Leggi settings_handler.py
with open('handlers/settings_handler.py', 'r') as f:
    content = f.read()

# Aggiungi le funzioni mancanti per gestire i callback
additional_functions = '''

async def show_rank_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show rank selection keyboard"""
    await update_rank(update, context)

async def show_irpef_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show IRPEF selection keyboard"""
    await update_irpef(update, context)

async def handle_settings_personal_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle personal settings modification callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "settings_change_rank":
        await update_rank(update, context)
    elif data == "settings_change_irpef":
        await update_irpef(update, context)
    elif data == "settings_base_hours":
        await ask_base_hours(update, context)
    elif data == "settings_command":
        await ask_command(update, context)
    elif data == "back_to_settings":
        await settings_command(update, context)
'''

# Aggiungi le funzioni alla fine del file se non esistono
if 'handle_settings_personal_callbacks' not in content:
    content += additional_functions
    print("✅ Aggiunte funzioni callback per settings personali")

# Salva il file
with open('handlers/settings_handler.py', 'w') as f:
    f.write(content)

# Ora aggiorna main.py per registrare questi handler
print("\n📝 Aggiorno main.py con i nuovi handler...")

with open('main.py', 'r') as f:
    main_content = f.read()

# Trova dove aggiungere il nuovo handler
settings_handler_line = 'application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_"))'

if settings_handler_line in main_content:
    # Aggiungi dopo questo handler
    new_handlers = '''
    # Settings personal callbacks
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_change_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_base_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_command"))
    application.add_handler(CallbackQueryHandler(update_rank, pattern="^rank_"))
    application.add_handler(CallbackQueryHandler(update_irpef, pattern="^irpef_"))'''
    
    # Sostituisci
    main_content = main_content.replace(
        settings_handler_line,
        settings_handler_line + new_handlers
    )
    print("✅ Aggiunti handler specifici per settings")

# Assicurati che gli import siano corretti
if 'from handlers.settings_handler import' in main_content:
    import_line_start = main_content.find('from handlers.settings_handler import')
    import_line_end = main_content.find('\n', import_line_start)
    current_imports = main_content[import_line_start:import_line_end]
    
    # Aggiungi update_rank e update_irpef se mancanti
    imports_needed = ['settings_command', 'settings_callback', 'update_rank', 'update_irpef']
    new_import_line = 'from handlers.settings_handler import (\n    ' + ',\n    '.join(imports_needed) + '\n)'
    
    main_content = main_content[:import_line_start] + new_import_line + main_content[import_line_end:]
    print("✅ Aggiornati import in main.py")

# Salva main.py
with open('main.py', 'w') as f:
    f.write(main_content)

# Fix anche per gestire l'input di testo quando l'utente modifica comando o ore base
print("\n📝 Aggiungo handler per input testo...")

# Aggiungi message handler per input testo in main.py
text_handler = '''
    # Handler for text input in settings
    async def handle_settings_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text input for settings"""
        if context.user_data.get('waiting_for_command'):
            # User is entering command name
            command_name = update.message.text
            user_id = str(update.effective_user.id)
            
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                user.command = command_name
                db.commit()
                
                await update.message.reply_text(
                    f"✅ Comando aggiornato: <b>{command_name}</b>",
                    parse_mode='HTML'
                )
                context.user_data['waiting_for_command'] = False
            finally:
                db.close()
                
        elif context.user_data.get('waiting_for_base_hours'):
            # User is entering base hours
            try:
                hours = int(update.message.text)
                if 1 <= hours <= 24:
                    user_id = str(update.effective_user.id)
                    
                    db = SessionLocal()
                    try:
                        user = db.query(User).filter(User.telegram_id == user_id).first()
                        user.base_shift_hours = hours
                        db.commit()
                        
                        await update.message.reply_text(
                            f"✅ Turno base aggiornato: <b>{hours} ore</b>",
                            parse_mode='HTML'
                        )
                        context.user_data['waiting_for_base_hours'] = False
                    finally:
                        db.close()
                else:
                    await update.message.reply_text("❌ Inserisci un numero tra 1 e 24")
            except ValueError:
                await update.message.reply_text("❌ Inserisci un numero valido")
    
    # Add the text handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_settings_text_input
    ))'''

# Trova dove aggiungere questo handler
if 'application.add_handler(MessageHandler' not in main_content:
    # Aggiungi prima di run_polling
    run_polling_pos = main_content.find('application.run_polling()')
    if run_polling_pos > 0:
        main_content = main_content[:run_polling_pos] + text_handler + '\n\n    ' + main_content[run_polling_pos:]

# Salva di nuovo main.py
with open('main.py', 'w') as f:
    f.write(main_content)

print("✅ Aggiunto handler per input testo")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add handlers/settings_handler.py main.py", shell=True)
subprocess.run('git commit -m "fix: aggiunti tutti i callback handler per le impostazioni"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("\n⏰ Attendi 2-3 minuti per il deploy")
print("📱 Poi torna su Telegram e prova:")
print("   - 🎖️ Modifica grado")
print("   - 💰 Modifica IRPEF")
print("   - ⏰ Modifica turno base")
print("   - 🏛️ Modifica comando")
print("\nTutti i pulsanti dovrebbero funzionare ora!")
