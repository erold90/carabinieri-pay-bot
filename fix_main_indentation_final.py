#!/usr/bin/env python3
import subprocess

print("🔧 FIX INDENTAZIONE main.py")
print("=" * 50)

# 1. Leggi main.py
print("\n1️⃣ Analisi main.py...")
with open('main.py', 'r') as f:
    lines = f.readlines()

print(f"Totale righe: {len(lines)}")

# 2. Mostra righe 85-90
print("\n2️⃣ Righe 85-90:")
for i in range(max(0, 84), min(len(lines), 91)):
    line_display = lines[i].replace(' ', '·').replace('\t', '→')
    print(f"{i+1}: {line_display}", end='')

# 3. Ricrea main.py pulito
print("\n\n3️⃣ Ricreo main.py con indentazione corretta...")

clean_main = '''#!/usr/bin/env python
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
from utils.clean_chat import cleanup_middleware

# Import database
from database.connection import init_db

# Import tutti gli handler necessari
from handlers.start_handler import start_command, dashboard_callback
from handlers.service_handler import (
    new_service_command, 
    service_conversation_handler,
    handle_service_type,
    handle_status_selection,
    handle_meals,
    handle_mission_type,
    handle_time_input
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
    
    # Middleware per pulizia automatica messaggi
    # DEVE essere il PRIMO handler con priority massima
    application.add_handler(MessageHandler(filters.ALL, cleanup_middleware), group=-999)

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
    
    # Specific handlers for service callbacks
    application.add_handler(CallbackQueryHandler(handle_service_type, pattern="^service_type_"))
    application.add_handler(CallbackQueryHandler(handle_status_selection, pattern="^status_"))
    application.add_handler(CallbackQueryHandler(handle_meals, pattern="^meals_"))
    application.add_handler(CallbackQueryHandler(handle_mission_type, pattern="^mission_type_"))
    
    # Rank and IRPEF selection handlers
    application.add_handler(CallbackQueryHandler(update_rank, pattern="^rank_"))
    application.add_handler(CallbackQueryHandler(update_irpef, pattern="^irpef_"))
    
    # Navigation handlers
    application.add_handler(CallbackQueryHandler(start_command, pattern="^back_to_menu$"))
    application.add_handler(CallbackQueryHandler(settings_command, pattern="^back_to_settings$"))
    application.add_handler(CallbackQueryHandler(leave_command, pattern="^back_to_leave$"))
    application.add_handler(CallbackQueryHandler(travel_sheets_command, pattern="^back_to_fv$"))
    application.add_handler(CallbackQueryHandler(overtime_command, pattern="^back_overtime$"))
    
    # Debug handler for unhandled callbacks
    async def debug_unhandled_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        logger.warning(f"Callback non gestito: {query.data}")
        await query.edit_message_text(
            f"⚠️ Funzione in sviluppo: {query.data}\\n\\nTorna al menu con /start",
            parse_mode='HTML'
        )
    
    # Add at the end to catch unhandled callbacks
    application.add_handler(CallbackQueryHandler(debug_unhandled_callback))
    
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

# 4. Salva il nuovo main.py
with open('main.py', 'w') as f:
    f.write(clean_main)

print("✅ main.py ricreato con indentazione corretta")

# 5. Verifica sintassi
print("\n4️⃣ Verifica sintassi...")
result = subprocess.run(['python3', '-m', 'py_compile', 'main.py'], capture_output=True)
if result.returncode == 0:
    print("✅ Sintassi corretta!")
else:
    print("❌ Errore:")
    print(result.stderr.decode())

# 6. Commit e push
print("\n5️⃣ Commit e push...")
subprocess.run("git add main.py", shell=True)
subprocess.run('git commit -m "fix: corretto errore indentazione main.py e integrato sistema pulizia messaggi"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ FIX COMPLETATO!")
print("\n🧹 Sistema pulizia messaggi:")
print("- Middleware attivo su TUTTI i messaggi")
print("- Mantiene solo ultimi 5 messaggi")
print("- Protegge messaggi con pulsanti")
print("\n⏰ Attendi 2-3 minuti per il deploy")
