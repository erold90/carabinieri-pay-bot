#!/usr/bin/env python3
import subprocess

print("🔧 Creazione main.py pulito e corretto")
print("=" * 50)

# Main.py completo e corretto
main_content = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CarabinieriPayBot - Bot Telegram per il calcolo stipendi Carabinieri
Main entry point
"""

import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from dotenv import load_dotenv

# Import handlers
from handlers.start_handler import start_command, dashboard_callback
from handlers.service_handler import (
    new_service_command, 
    service_conversation_handler
)
from handlers.overtime_handler import (
    overtime_command,
    overtime_callback,
    paid_hours_command,
    accumulation_command
)
from handlers.travel_sheet_handler import (
    travel_sheets_command,
    travel_sheet_callback,
    register_payment_command
)
from handlers.leave_handler import (
    leave_command,
    leave_callback,
    add_leave_command,
    plan_leave_command
)
from handlers.report_handler import (
    today_command,
    yesterday_command,
    week_command,
    month_command,
    year_command,
    export_command
)
from handlers.settings_handler import (
    settings_command,
    settings_callback,
    update_rank,
    update_irpef
)

# Import database
from database.connection import init_db

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Initialize database
    init_db()
    
    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("nuovo", new_service_command))
    application.add_handler(CommandHandler("scorta", new_service_command))
    application.add_handler(CommandHandler("straordinari", overtime_command))
    application.add_handler(CommandHandler("ore_pagate", paid_hours_command))
    application.add_handler(CommandHandler("accumulo", accumulation_command))
    application.add_handler(CommandHandler("fv", travel_sheets_command))
    application.add_handler(CommandHandler("fv_pagamento", register_payment_command))
    application.add_handler(CommandHandler("licenze", leave_command))
    application.add_handler(CommandHandler("inserisci_licenza", add_leave_command))
    application.add_handler(CommandHandler("pianifica", plan_leave_command))
    application.add_handler(CommandHandler("oggi", today_command))
    application.add_handler(CommandHandler("ieri", yesterday_command))
    application.add_handler(CommandHandler("settimana", week_command))
    application.add_handler(CommandHandler("mese", month_command))
    application.add_handler(CommandHandler("anno", year_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("impostazioni", settings_command))
    
    # Conversation handlers
    application.add_handler(service_conversation_handler)
    
    # Callback query handlers
    application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="^dashboard_"))
    application.add_handler(CallbackQueryHandler(overtime_callback, pattern="^overtime_"))
    application.add_handler(CallbackQueryHandler(travel_sheet_callback, pattern="^fv_"))
    application.add_handler(CallbackQueryHandler(leave_callback, pattern="^leave_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_"))
    
    # Rank and IRPEF selection handlers
    application.add_handler(CallbackQueryHandler(update_rank, pattern="^rank_"))
    application.add_handler(CallbackQueryHandler(update_irpef, pattern="^irpef_"))
    
    # Back navigation callbacks
    application.add_handler(CallbackQueryHandler(start_command, pattern="^back_to_menu$"))
    application.add_handler(CallbackQueryHandler(settings_command, pattern="^back_to_settings$"))
    application.add_handler(CallbackQueryHandler(leave_command, pattern="^back_to_leave$"))
    application.add_handler(CallbackQueryHandler(travel_sheets_command, pattern="^back_to_fv$"))
    application.add_handler(CallbackQueryHandler(overtime_command, pattern="^back_overtime$"))
    
    # Error handler
    async def error_handler(update: Update, context):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting CarabinieriPayBot...")
    application.run_polling()

if __name__ == '__main__':
    main()
'''

# Salva il nuovo main.py
with open('main.py', 'w') as f:
    f.write(main_content)

print("✅ main.py creato correttamente!")

# Verifica che settings_handler abbia le funzioni necessarie
print("\n📝 Verifico settings_handler.py...")

try:
    with open('handlers/settings_handler.py', 'r') as f:
        settings_content = f.read()
    
    # Controlla se mancano le funzioni
    functions_needed = ['update_rank', 'update_irpef']
    missing_functions = []
    
    for func in functions_needed:
        if f'async def {func}' not in settings_content:
            missing_functions.append(func)
    
    if missing_functions:
        print(f"⚠️ Funzioni mancanti in settings_handler: {missing_functions}")
        print("Le aggiungerò...")
        
        # Aggiungi le funzioni mancanti
        additional_code = '''

async def update_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update user rank"""
    query = update.callback_query
    await query.answer()
    
    rank_index = int(query.data.replace("rank_", ""))
    selected_rank = RANKS[rank_index]
    
    user_id = str(query.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        user.rank = selected_rank
        db.commit()
        
        await query.edit_message_text(
            f"✅ Grado aggiornato: <b>{selected_rank}</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Torna alle impostazioni", callback_data="settings_personal")]
            ])
        )
        
    except Exception as e:
        print(f"[ERROR] Aggiornamento grado: {e}")
        await query.edit_message_text(
            "❌ Errore nel salvataggio. Riprova.",
            parse_mode='HTML'
        )
    finally:
        db.close()

async def update_irpef(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update IRPEF rate"""
    query = update.callback_query
    await query.answer()
    
    rate = int(query.data.replace("irpef_", ""))
    
    user_id = str(query.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        user.irpef_rate = rate / 100
        db.commit()
        
        await query.edit_message_text(
            f"✅ Aliquota IRPEF aggiornata: <b>{rate}%</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Torna alle impostazioni", callback_data="settings_personal")]
            ])
        )
        
    except Exception as e:
        print(f"[ERROR] Aggiornamento IRPEF: {e}")
        await query.edit_message_text(
            "❌ Errore nel salvataggio. Riprova.",
            parse_mode='HTML'
        )
    finally:
        db.close()
'''
        
        with open('handlers/settings_handler.py', 'a') as f:
            f.write(additional_code)
        
        print("✅ Funzioni aggiunte a settings_handler.py")
    else:
        print("✅ Tutte le funzioni necessarie sono presenti")
        
except Exception as e:
    print(f"❌ Errore nella verifica: {e}")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add main.py handlers/settings_handler.py", shell=True)
subprocess.run('git commit -m "fix: corretto main.py e aggiunte funzioni mancanti"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("📱 Il bot dovrebbe ripartire correttamente")
print("🎖️ I pulsanti per selezionare il grado dovrebbero funzionare!")
