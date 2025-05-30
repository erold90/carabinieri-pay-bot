from telegram.ext import ContextTypes
from telegram import Update
#!/usr/bin/env python3
import subprocess

print("🔧 Fix pulsanti gradi e clean chat")
print("=" * 50)

# 1. Fix handler per i pulsanti dei gradi
print("\n1️⃣ Aggiungo handler per callback rank_...")

with open('main.py', 'r') as f:
    main_content = f.read()

# Aggiungi import per update_rank
if 'from handlers.settings_handler import' in main_content:
    # Trova la riga degli import da settings_handler
    import_start = main_content.find('from handlers.settings_handler import')
    import_end = main_content.find('\n', import_start)
    current_imports = main_content[import_start:import_end]
    
    # Aggiungi update_rank se mancante
    if 'update_rank' not in current_imports:
        new_imports = current_imports.rstrip(')') + ',\n    update_rank,\n    update_irpef\n)'
        main_content = main_content.replace(current_imports, new_imports)
        print("✅ Aggiunto import update_rank e update_irpef")

# Aggiungi handler per rank_ e irpef_ callbacks
rank_handler = '''    # Rank and IRPEF selection handlers
    application.add_handler(CallbackQueryHandler(update_rank, pattern="^rank_"))
    application.add_handler(CallbackQueryHandler(update_irpef, pattern="^irpef_"))
    '''

# Trova dove inserire (dopo gli altri callback handler)
last_callback = main_content.rfind('application.add_handler(CallbackQueryHandler')
if last_callback > 0 and 'pattern="^rank_"' not in main_content:
    # Trova la fine della riga
    line_end = main_content.find('\n', last_callback)
    main_content = main_content[:line_end+1] + rank_handler + main_content[line_end+1:]
    print("✅ Aggiunto handler per rank_ e irpef_")

# 2. Fix clean chat - disabilitiamolo temporaneamente
print("\n2️⃣ Disabilito temporaneamente clean chat...")

# Rimuovi i wrapper clean_chat_command
main_content = main_content.replace('clean_chat_command(', '')
main_content = main_content.replace(')', '))', 1)  # Fix parentesi

# Commenta gli import di clean chat
main_content = main_content.replace(
    'from utils.clean_chat import chat_cleaner',
    '# from utils.clean_chat import chat_cleaner'
)
main_content = main_content.replace(
    'from utils.handler_decorators import clean_chat_command, clean_chat_callback',
    '# from utils.handler_decorators import clean_chat_command, clean_chat_callback'
)

# Salva main.py
with open('main.py', 'w') as f:
    f.write(main_content)

print("✅ main.py aggiornato")

# 3. Assicurati che update_rank sia definito correttamente in settings_handler
print("\n3️⃣ Verifico settings_handler.py...")

settings_addition = '''
async def update_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update user rank"""
    query = update.callback_query
    await query.answer()
    
    try:
        rank_index = int(query.data.replace("rank_", ""))
        selected_rank = RANKS[rank_index]
        
        user_id = str(query.from_user.id)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.rank = selected_rank
                db.commit()
                
                await query.edit_message_text(
                    f"✅ Grado aggiornato: <b>{selected_rank}</b>",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Torna alle impostazioni", callback_data="settings_personal")]
                    ])
                )
            else:
                await query.edit_message_text(
                    "❌ Errore: utente non trovato",
                    parse_mode='HTML'
                )
        finally:
            db.close()
            
    except Exception as e:
        print(f"Errore in update_rank: {e}")
        await query.edit_message_text(
            "❌ Si è verificato un errore",
            parse_mode='HTML'
        )

async def update_irpef(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update IRPEF rate"""
    query = update.callback_query
    await query.answer()
    
    try:
        rate = int(query.data.replace("irpef_", ""))
        
        user_id = str(query.from_user.id)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if user:
                user.irpef_rate = rate / 100
                db.commit()
                
                await query.edit_message_text(
                    f"✅ Aliquota IRPEF aggiornata: <b>{rate}%</b>",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Torna alle impostazioni", callback_data="settings_personal")]
                    ])
                )
            else:
                await query.edit_message_text(
                    "❌ Errore: utente non trovato",
                    parse_mode='HTML'
                )
        finally:
            db.close()
            
    except Exception as e:
        print(f"Errore in update_irpef: {e}")
        await query.edit_message_text(
            "❌ Si è verificato un errore",
            parse_mode='HTML'
        )
'''

# Controlla se le funzioni esistono già
with open('handlers/settings_handler.py', 'r') as f:
    settings_content = f.read()

if 'async def update_rank' not in settings_content:
    # Aggiungi alla fine del file
    with open('handlers/settings_handler.py', 'a') as f:
        f.write('\n\n' + settings_addition)
    print("✅ Aggiunte funzioni update_rank e update_irpef")

# 4. Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add main.py handlers/settings_handler.py", shell=True)
subprocess.run('git commit -m "fix: handler per selezione grado e disabilitato temporaneamente clean chat"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("\n📝 Modifiche:")
print("1. Aggiunti handler per i pulsanti dei gradi")
print("2. Disabilitato temporaneamente clean chat")
print("3. I pulsanti dei gradi dovrebbero funzionare ora!")
