#!/usr/bin/env python
# Deploy forzato: 2025-05-31 00:49:55
# -*- coding: utf-8 -*-
"""
CarabinieriPayBot - Bot Telegram per il calcolo stipendi Carabinieri
Main entry point
"""

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CarabinieriPayBot - Bot Telegram per il calcolo stipendi Carabinieri
Main entry point
"""

import logging
import os
from telegram import Update
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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
    handle_time_input,
    handle_meal_selection
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
from handlers.rest_handler import rest_command, rest_callback
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
    update_irpef,
    handle_text_input,
    handle_leave_edit,
    handle_route_action,
    handle_patron_saint,
    handle_reminder_time,
    toggle_notification
)
from handlers.setup_handler import setup_conversation_handler

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Handler per callback non implementati
async def handle_missing_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler generico per callback non implementati"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    logger.warning(f"Callback non implementato: {callback_data}")
    
    # Risposte specifiche per tipo di callback
    responses = {
        "meal_lunch": "🍽️ Selezione pasto...",
        "meal_dinner": "🍽️ Selezione pasto...",
        "meal_confirm": "✅ Conferma selezione pasti",
        "back": "⬅️ Torna indietro",
        "setup_start": "⚙️ Avvio configurazione..."
    }
    
    response_text = responses.get(callback_data, "⚠️ Funzione in sviluppo")
    
    try:
        await query.answer(response_text)
    except:
        await query.answer("✅")

# Handler per navigazione indietro
async def handle_back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back navigation"""
    query = update.callback_query
    await query.answer()
    
    destination = query.data.replace('back_', '')
    
    # Route to appropriate handler
    if destination == 'to_menu':
        await start_command(update, context)
    elif destination == 'to_settings':
        from handlers.settings_handler import settings_command
        await settings_command(update, context)
    elif destination == 'to_leave':
        from handlers.leave_handler import leave_command
        await leave_command(update, context)
    elif destination == 'to_fv':
        from handlers.travel_sheet_handler import travel_sheets_command
        await travel_sheets_command(update, context)
    elif destination == 'overtime':
        from handlers.overtime_handler import overtime_command
        await overtime_command(update, context)
    elif destination == 'to_rest':
        from handlers.rest_handler import rest_command
        await rest_command(update, context)
    else:
        # Default
        await query.edit_message_text(
            "⬅️ Tornando al menu principale...",
            parse_mode='HTML'
        )
        await start_command(update, context)

# Handler debug per callback non gestiti
async def debug_unhandled_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug handler for unhandled callbacks"""
    query = update.callback_query
    await query.answer()
    logger.warning(f"Callback non gestito: {query.data}")
    await query.answer(f"Debug: {query.data}")



# Debug handler - rimuovere in produzione
def main():
    """Start the bot."""
    # Initialize database
    init_db()
    
    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))).build()
    
    # Middleware per pulizia automatica messaggi
    # DEVE essere il PRIMO handler con priority massima

    # DEBUG: Log TUTTI gli update ricevuti
# Debug handler for unhandled callbacks
    async def debug_unhandled_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        logger.warning(f"Callback non gestito: {query.data}")
        await query.edit_message_text(
            f"⚠️ Funzione in sviluppo: {query.data}\n\nTorna al menu con /start",
            parse_mode='HTML'
        )
    
    # Add at the end to catch unhandled callbacks
    application.add_handler(CallbackQueryHandler(debug_unhandled_callback))

    # Middleware pulizia chat - eseguito DOPO tutti gli handler

    
    # Error handler
    async def error_handler(update: Update, context):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting CarabinieriPayBot...")
    # start_notification_system(application.bot)
    logger.info("Bot started and polling for updates...")
    # logger.info(f"Bot username: @{application.bot.username if hasattr(application.bot, 'username') else 'Unknown'}")
    application.run_polling()

if __name__ == '__main__':
    main()
