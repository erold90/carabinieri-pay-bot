#!/usr/bin/env python3
import subprocess

print("🔧 Fix callback handlers mancanti")
print("=" * 50)

# 1. Aggiungiamo i callback mancanti in main.py
print("\n1️⃣ Analizzo main.py per callback mancanti...")

with open('main.py', 'r') as f:
    main_content = f.read()

# Callback patterns che dovrebbero essere presenti
required_callbacks = [
    ('back_to_menu', 'start_command'),
    ('back_to_settings', 'settings_command'),
    ('back_to_leave', 'leave_command'),
    ('back_to_fv', 'travel_sheets_command'),
    ('back_overtime', 'overtime_command'),
    ('setup_start', 'setup_start_handler'),
    ('settings_change_rank', 'show_rank_selection'),
    ('settings_change_irpef', 'show_irpef_selection'),
]

# Aggiungi handler per i callback "back"
additional_handlers = '''
# Additional callback handlers for navigation
async def handle_back_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all back navigation callbacks"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "back_to_menu":
        await start_command(update, context)
    elif callback_data == "back_to_settings":
        await settings_command(update, context)
    elif callback_data == "back_to_leave":
        await leave_command(update, context)
    elif callback_data == "back_to_fv":
        await travel_sheets_command(update, context)
    elif callback_data == "back_overtime":
        await overtime_command(update, context)

async def handle_setup_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle setup callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "setup_start":
        # Start setup wizard
        text = "⚙️ <b>CONFIGURAZIONE INIZIALE</b>\\n\\n"
        text += "Procediamo con la configurazione.\\n\\n"
        text += "Usa /impostazioni per configurare i tuoi dati."
        
        await query.edit_message_text(text, parse_mode='HTML')
'''

# Trova dove aggiungere i nuovi handler (prima di main())
main_func_pos = main_content.find('def main():')
if main_func_pos > 0:
    # Inserisci i nuovi handler prima di main()
    main_content = main_content[:main_func_pos] + additional_handlers + '\n\n' + main_content[main_func_pos:]

# Aggiungi i callback handler nella funzione main()
handlers_to_add = '''
    # Back navigation handlers
    application.add_handler(CallbackQueryHandler(handle_back_callbacks, pattern="^back_to_"))
    application.add_handler(CallbackQueryHandler(handle_setup_callbacks, pattern="^setup_"))
    '''

# Trova dove aggiungere i handler (dopo gli altri add_handler)
last_handler_pos = main_content.rfind('application.add_handler(CallbackQueryHandler')
if last_handler_pos > 0:
    # Trova la fine della riga
    line_end = main_content.find('\n', last_handler_pos)
    main_content = main_content[:line_end] + '\n' + handlers_to_add + main_content[line_end:]

# Salva main.py aggiornato
with open('main.py', 'w') as f:
    f.write(main_content)

print("✅ Aggiunti handler per callback di navigazione in main.py")

# 2. Fix travel_sheet_handler callbacks
print("\n2️⃣ Fix callback in travel_sheet_handler.py...")

# Aggiungi la funzione mancante back_to_fv se non esiste
with open('handlers/travel_sheet_handler.py', 'r') as f:
    travel_content = f.read()

if 'async def back_to_fv' not in travel_content:
    # Aggiungi alla fine del file
    travel_content += '''

async def back_to_fv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to travel sheets main menu"""
    await travel_sheets_command(update, context)
'''
    
    with open('handlers/travel_sheet_handler.py', 'w') as f:
        f.write(travel_content)
    
    print("✅ Aggiunta funzione back_to_fv")

# 3. Commit e push
print("\n3️⃣ Commit e push delle modifiche...")
subprocess.run("git add main.py handlers/travel_sheet_handler.py", shell=True)
subprocess.run('git commit -m "fix: aggiunti callback handler mancanti per navigazione"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("\n⏰ Attendi 2-3 minuti per il deploy")
print("📱 Poi prova di nuovo i pulsanti su Telegram")
print("\n💡 Tutti i pulsanti dovrebbero funzionare ora!")
