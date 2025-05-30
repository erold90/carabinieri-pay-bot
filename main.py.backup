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
    settings_command,
    settings_callback
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
        text = "⚙️ <b>CONFIGURAZIONE INIZIALE</b>\n\n"
        text += "Procediamo con la configurazione.\n\n"
        text += "Usa /impostazioni per configurare i tuoi dati."
        
        await query.edit_message_text(text, parse_mode='HTML')


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
    # Settings personal callbacks
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_change_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_base_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_command"))
    application.add_handler(CallbackQueryHandler(update_rank, pattern="^rank_"))
    application.add_handler(CallbackQueryHandler(update_irpef, pattern="^irpef_"))

    # Back navigation handlers
    application.add_handler(CallbackQueryHandler(handle_back_callbacks, pattern="^back_to_"))
    application.add_handler(CallbackQueryHandler(handle_setup_callbacks, pattern="^setup_"))
    
    
    # Error handler
    async def error_handler(update: Update, context):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, context.error)

    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting CarabinieriPayBot...")
    
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
    ))

    application.run_polling()

if __name__ == '__main__':
    main()