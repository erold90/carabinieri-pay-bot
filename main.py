#!/usr/bin/env python
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
from handlers.settings_handler import settings_callback
from handlers.leave_handler import leave_callback
from handlers.travel_sheet_handler import travel_sheet_callback
from handlers.overtime_handler import overtime_callback
from handlers.report_handler import month_command
from handlers.service_handler import handle_service_type, handle_status_selection, handle_meals, handle_meal_selection, handle_mission_type
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
    
   # Debug handler per callback non gestiti
   async def debug_unhandled_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
       query = update.callback_query
       await query.answer()
       logger.warning(f"Callback non gestito: {query.data}")
       await query.edit_message_text(
           f"⚠️ Funzione in sviluppo: {query.data}

Torna al menu con /start",
           parse_mode='HTML'
       )
   
   # Aggiungi alla fine per catturare callback non gestiti
   application.add_handler(CallbackQueryHandler(debug_unhandled_callback))

    
    # Additional callback handlers for all buttons
    application.add_handler(CallbackQueryHandler(new_service_command, pattern="^dashboard_new_service$|^dashboard_new_escort$"))
    application.add_handler(CallbackQueryHandler(month_command, pattern="^dashboard_report$"))
    application.add_handler(CallbackQueryHandler(overtime_command, pattern="^dashboard_overtime$"))
    application.add_handler(CallbackQueryHandler(travel_sheets_command, pattern="^dashboard_travel_sheets$"))
    application.add_handler(CallbackQueryHandler(leave_command, pattern="^dashboard_leaves$"))
    application.add_handler(CallbackQueryHandler(settings_command, pattern="^dashboard_settings$"))
    application.add_handler(CallbackQueryHandler(handle_service_type, pattern="^service_type_LOCAL$|^service_type_ESCORT$|^service_type_MISSION$"))
    application.add_handler(CallbackQueryHandler(handle_status_selection, pattern="^status_normal$|^status_leave$|^status_rest$|^status_recovery$|^status_other$"))
    application.add_handler(CallbackQueryHandler(handle_meals, pattern="^meals_0$|^meals_1$|^meals_2$"))
    application.add_handler(CallbackQueryHandler(handle_meal_selection, pattern="^meal_lunch$|^meal_dinner$"))
    application.add_handler(CallbackQueryHandler(handle_mission_type, pattern="^mission_type_ordinary$|^mission_type_forfeit$"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_personal$|^settings_leaves$|^settings_location$|^settings_notifications$|^settings_change_rank$|^settings_change_irpef$|^settings_command$|^settings_base_hours$"))
    application.add_handler(CallbackQueryHandler(overtime_callback, pattern="^overtime_detail$|^overtime_simulate$|^overtime_paid$|^overtime_history$"))
    application.add_handler(CallbackQueryHandler(travel_sheet_callback, pattern="^fv_register_payment$|^fv_annual_report$|^fv_search$|^fv_export$"))
    application.add_handler(CallbackQueryHandler(leave_callback, pattern="^leave_add$|^leave_plan$|^leave_report$|^leave_config$|^leave_type_current$|^leave_type_previous$|^leave_type_sick$|^leave_type_blood$|^leave_type_104$|^leave_type_study$|^leave_type_marriage$|^leave_type_other$|^leave_confirm$"))

    application.run_polling()

if __name__ == '__main__':
    main()
