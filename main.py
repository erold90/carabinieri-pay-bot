#!/usr/bin/env python
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
from services.notification_service import start_notification_system

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
,
    handle_meal_selection)
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
from handlers.report_handler import ()
# from handlers.export_handler import generate_excel_export  # TODO: verificare
    today_command,
    yesterday_command,
    week_command,
    month_command,
    year_command,
    export_command
)
from handlers.settings_handler import ()
    handle_leave_edit,
    handle_reminder_time,
    toggle_notification,
    handle_route_action,
    handle_patron_saint
    settings_command,
    settings_callback,
    update_rank,
    update_irpef,
    handle_text_input,
    settings_command,
    handle_patron_saint
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

# Handler per callback mancanti
async def handle_missing_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler generico per callback non implementati"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Log per debug
    logger.warning(f"Callback non implementato: {callback_data}")
    
    # Risposte specifiche per tipo di callback
    responses = {
        "meal_lunch": "🍽️ Gestione pasti in aggiornamento...",
        "meal_confirm": "🍽️ Gestione pasti in aggiornamento...",
        "meal_dinner": "🍽️ Gestione pasti in aggiornamento...",
        "back": "🔧 Funzione back in sviluppo...",
        "setup_start": "🔧 Funzione setup in sviluppo...",
        "([^": "🔧 Funzione ([^ in sviluppo...",
        # Default
        "default": "⚠️ Funzione non ancora disponibile.\n\nTorna al menu principale con /start"
    }
    
    # Ottieni la risposta appropriata
    response_text = responses.get(callback_data, responses["default"])
    
    # Invia la risposta
    try:
        await query.edit_message_text(
            response_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu Principale", callback_data="back_to_menu")]
            ])
        )
    except:
        # Se edit fallisce, prova con un nuovo messaggio
        await query.message.reply_text(
            response_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu Principale", callback_data="back_to_menu")]
            ])
        )



# === FUNZIONI DI SUPPORTO PER CALLBACK ===

async def handle_time_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle time selection callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith('start_time_'):
        hour = int(data.replace('start_time_', ''))
        await query.answer(f"Inizio: {hour:02d}:00")
    elif data.startswith('end_time_'):
        hour = int(data.replace('end_time_', ''))
        await query.answer(f"Fine: {hour:02d}:00")

async def handle_back_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all back navigation"""
    query = update.callback_query
    await query.answer()
    
    destination = query.data.replace('back_', '')
    
    # Route to appropriate handler
    if destination == 'to_menu':
        await start_command(update, context)
    elif destination == 'to_settings':
        await settings_command(update, context)
    elif destination == 'to_leave':
        await leave_command(update, context)
    elif destination == 'to_fv':
        await travel_sheets_command(update, context)
    elif destination == 'overtime':
        await overtime_command(update, context)
    else:
        # Default back action
        await query.edit_message_text(
            "⬅️ Tornando indietro...",
            parse_mode='HTML'
        )

async def handle_generic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str):
    """Handle generic callbacks"""
    query = update.callback_query
    
    # Log per debug
    print(f"[DEBUG] Callback generico: {callback_data}")
    
    # Risposte predefinite per callback comuni
    responses = {
        'setup_start': '⚙️ Avvio configurazione...',
        'month_': '📅 Selezione mese...',
        'add_route': '➕ Aggiunta percorso...',
        'remove_route': '➖ Rimozione percorso...',
        'set_patron_saint': '📅 Impostazione Santo Patrono...',
        'change_reminder_time': '⏰ Cambio orario notifiche...',
    }
    
    # Cerca risposta appropriata
    response = '✅'
    for key, msg in responses.items():
        if callback_data.startswith(key):
            response = msg
            break
    
    await query.answer(response)
    
    # Se necessario, aggiorna il messaggio
    if callback_data in ['setup_start', 'add_route', 'remove_route']:
        await query.edit_message_text(
            f"{response}\n\nFunzione in sviluppo.",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Indietro", callback_data="back")]
            ])
        )



    # Handler per input di testo in vari contesti
    async def handle_general_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text inputs based on context"""
        user_data = context.user_data
        
        # Overtime: ore pagate
        if user_data.get('waiting_for_paid_hours'):
            from handlers.overtime_handler import handle_paid_hours_input
            await handle_paid_hours_input(update, context)
            
        # Travel sheets: selezione FV da pagare
        elif user_data.get('waiting_for_fv_selection'):
            from handlers.travel_sheet_handler import handle_travel_sheet_selection
            await handle_travel_sheet_selection(update, context)
            
        # Travel sheets: ricerca
        elif user_data.get('waiting_for_fv_search'):
            from handlers.travel_sheet_handler import handle_travel_sheet_search
            await handle_travel_sheet_search(update, context)
            
        # Settings: vari input
        elif user_data.get('waiting_for_command') or user_data.get('waiting_for_base_hours'):
            from handlers.settings_handler import handle_text_input
            await handle_text_input(update, context)
            
        # Leave: modifica valori
        elif user_data.get('waiting_for_leave_value'):
            from handlers.leave_handler import handle_leave_value_input
            await handle_leave_value_input(update, context)
            
        # Routes: nome percorso
        elif user_data.get('adding_route'):
            from handlers.leave_handler import handle_route_name_input
            await handle_route_name_input(update, context)
            
        # Routes: km percorso
        elif user_data.get('adding_route_km'):
            from handlers.leave_handler import handle_route_km_input
            await handle_route_km_input(update, context)
            
        # Patron saint
        elif user_data.get('setting_patron_saint'):
            from handlers.leave_handler import handle_patron_saint_input
            await handle_patron_saint_input(update, context)
            
        # Reminder time
        elif user_data.get('setting_reminder_time'):
            from handlers.leave_handler import handle_reminder_time_input
            await handle_reminder_time_input(update, context)
    
    # Aggiungi handler generale per testo PRIMA dei conversation handler
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_general_text_input
    ), group=1)


def main():
    """Start the bot."""
    # Initialize database
    init_db()
    
    # Create the Application
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))).build()
    
    # Middleware per pulizia automatica messaggi
    # DEVE essere il PRIMO handler con priority massima
    application.add_handler(MessageHandler(filters.ALL, cleanup_middleware), group=-999)

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
    application.add_handler(CallbackQueryHandler(
        handle_leave_edit, pattern="^edit_.*_leave"
    ))
    
    # Route handlers
    application.add_handler(CallbackQueryHandler(
        handle_route_action, pattern="^(add|remove)_route$"
    ))
    
    # Patron saint handler
    application.add_handler(CallbackQueryHandler(
        handle_patron_saint, pattern="^set_patron_saint$"
    ))
    
    # Notification time handler
    application.add_handler(CallbackQueryHandler(
        handle_reminder_time, pattern="^change_reminder_time$"
    ))

    
    # === HANDLER PER TUTTI I CALLBACK MANCANTI ===

    # toggle_ callbacks (4 items)
    application.add_handler(CallbackQueryHandler(
        toggle_notification,
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
    application.add_handler(CallbackQueryHandler(
        handle_leave_edit, 
        pattern="^(edit_current_leave_total|edit_current_leave_used|edit_previous_leave)$"
    ))
    
    # Handler per gestione percorsi
    application.add_handler(CallbackQueryHandler(
        handle_route_action, 
        pattern="^(add_route|remove_route)$"
    ))
    
    # Handler per santo patrono
    application.add_handler(CallbackQueryHandler(
        handle_patron_saint, 
        pattern="^set_patron_saint$"
    ))
    
    # Handler per orario notifiche
    application.add_handler(CallbackQueryHandler(
        handle_reminder_time, 
        pattern="^change_reminder_time$"
    ))
    
    # Handler per toggle notifiche
    application.add_handler(CallbackQueryHandler(
        toggle_notification,
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
    
    # Error handler
    async def error_handler(update: Update, context):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting CarabinieriPayBot...")
    start_notification_system(application.bot)
    application.run_polling()

if __name__ == '__main__':
    main()
