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
    async def debug_log(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message:
            logger.info(f"[DEBUG] Messaggio ricevuto: {update.message.text} da {update.effective_user.id}")
        elif update.callback_query:
            logger.info(f"[DEBUG] Callback ricevuto: {update.callback_query.data}")
        # NON blocca il messaggio, lascia che continui
    
    application.add_handler(MessageHandler(filters.ALL, debug_log), group=-100)
    logger.info("Debug handler registrato")
    
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cleanup_middleware), group=999)

    application.add_handler(CommandHandler("nuovo", new_service_command))
    application.add_handler(CommandHandler("scorta", new_service_command))
    application.add_handler(CommandHandler("straordinari", overtime_command))
    application.add_handler(CommandHandler("ore_pagate", paid_hours_command))
    application.add_handler(CommandHandler("accumulo", accumulation_command))
    application.add_handler(CommandHandler("fv", travel_sheets_command))
    application.add_handler(CommandHandler("fv_pagamento", register_payment_command))
    application.add_handler(CommandHandler("licenze", leave_command))
    application.add_handler(CommandHandler("riposi", rest_command))
    application.add_handler(CommandHandler("inserisci_licenza", add_leave_command))
    application.add_handler(CommandHandler("pianifica", plan_leave_command))
    application.add_handler(CommandHandler("oggi", today_command))
    application.add_handler(CommandHandler("ieri", yesterday_command))
    application.add_handler(CommandHandler("settimana", week_command))
    application.add_handler(CommandHandler("mese", month_command))
    application.add_handler(CommandHandler("anno", year_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("impostazioni", settings_command))

    # Text input handler for settings
    
    # Conversation handlers
    application.add_handler(service_conversation_handler)
    application.add_handler(setup_conversation_handler)
    
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

    application.add_handler(CallbackQueryHandler(handle_missing_callbacks, pattern="^meal_"))
    application.add_handler(CallbackQueryHandler(handle_missing_callbacks, pattern="^setup_"))
    application.add_handler(CallbackQueryHandler(handle_missing_callbacks, pattern="^back_"))
    application.add_handler(CallbackQueryHandler(handle_missing_callbacks, pattern="^back$"))
    application.add_handler(CallbackQueryHandler(handle_missing_callbacks, pattern="^back$"))

    # Leave edit handlers
    application.add_handler(CallbackQueryHandler(handle_leave_edit, pattern="^(edit_current_leave_total|edit_current_leave_used|edit_previous_leave)$"))
    
    # Route handlers
    application.add_handler(CallbackQueryHandler(handle_route_action, pattern="^(add_route|remove_route)$"))
    
    # Patron saint handler
    application.add_handler(CallbackQueryHandler(handle_patron_saint, pattern="^set_patron_saint$"))
    
    # Notification time handler
    application.add_handler(CallbackQueryHandler(handle_patron_saint, pattern="^set_patron_saint$"))

    # === HANDLER PER TUTTI I CALLBACK MANCANTI ===

    # toggle_ callbacks (4 items)
    application.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), 
        pattern="^(toggle_travel_sheet|toggle_leave_expiry|toggle_overtime_limit|toggle_daily_reminder)$"
    ))

    # edit_ callbacks (3 items)
    application.add_handler(CallbackQueryHandler(
        lambda u,c: u.callback_query.answer('✅'),
        pattern="^(edit_current_leave_total|edit_previous_leave|edit_current_leave_used)$"
    ))

    # add_ callbacks (1 items)
    application.add_handler(CallbackQueryHandler(
        lambda u,c: u.callback_query.answer('✅'),
        pattern="^add_route$"
    ))

    # remove_ callbacks (1 items)
    application.add_handler(CallbackQueryHandler(
        lambda u,c: u.callback_query.answer('✅'),
        pattern="^remove_route$"
    ))

    # Handler per callback di modifica licenze
    application.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), 
        pattern="^(edit_current_leave_total|edit_current_leave_used|edit_previous_leave)$"
    ))
    
    # Handler per gestione percorsi
    application.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), 
        pattern="^(add_route|remove_route)$"
    ))
    
    # Handler per santo patrono
    application.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), 
        pattern="^set_patron_saint$"
    ))
    
    # Handler per orario notifiche
    application.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), 
        pattern="^change_reminder_time$"
    ))
    
    # Handler per toggle notifiche
    application.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.answer(), 
        pattern="^(toggle_daily_reminder|toggle_overtime_limit|toggle_leave_expiry|toggle_travel_sheet)$"
    ))
    
    # Handler per selezione pasti
    application.add_handler(CallbackQueryHandler(
        handle_meal_selection,
        pattern="^(meal_lunch|meal_dinner|meal_confirm)$"
    ))

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
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, cleanup_middleware), group=999)
    
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
