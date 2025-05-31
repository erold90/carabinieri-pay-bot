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
from telegram.error import RetryAfter, TimedOut, NetworkError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from telegram.ext import CommandHandler
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

# Import handler mancanti per input testuali
from handlers.leave_handler import (
    handle_leave_value_input,
    handle_route_name_input, 
    handle_route_km_input,
    handle_patron_saint_input,
    handle_reminder_time_input
)
from handlers.travel_sheet_handler import (
    handle_travel_sheet_selection,
    handle_travel_sheet_search
)
from handlers.overtime_handler import handle_paid_hours_input
from handlers.export_handler import generate_excel_export

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




async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log tutti i messaggi per debug"""
    if update.message:
        logger.info(f"📨 MESSAGGIO RICEVUTO: '{update.message.text}' da @{update.message.from_user.username if update.message.from_user else 'Unknown'}")
        if update.message.text and update.message.text.startswith('/'):
            logger.info(f"   È UN COMANDO: {update.message.text}")
    elif update.callback_query:
        logger.info(f"🔘 CALLBACK RICEVUTO: '{update.callback_query.data}'")

# Debug handler - rimuovere in produzione

# Handler unificato per tutti gli input testuali
async def handle_all_text_inputs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler per tutti gli input testuali"""
    user_data = context.user_data
    
    # Leave values
    if user_data.get('waiting_for_leave_value'):
        return await handle_leave_value_input(update, context)
    
    # Route names
    elif user_data.get('adding_route'):
        return await handle_route_name_input(update, context)
    
    # Route km
    elif user_data.get('adding_route_km'):
        return await handle_route_km_input(update, context)
    
    # Patron saint
    elif user_data.get('setting_patron_saint'):
        return await handle_patron_saint_input(update, context)
    
    # Reminder time
    elif user_data.get('setting_reminder_time'):
        return await handle_reminder_time_input(update, context)
    
    # Travel sheet selection
    elif user_data.get('waiting_for_fv_selection'):
        return await handle_travel_sheet_selection(update, context)
    
    # FV search
    elif user_data.get('waiting_for_fv_search'):
        return await handle_travel_sheet_search(update, context)
    
    # Paid hours
    elif user_data.get('waiting_for_paid_hours'):
        return await handle_paid_hours_input(update, context)
    
    # Command input (da settings)
    elif user_data.get('waiting_for_command'):
        return await handle_text_input(update, context)
    
    # Base hours input
    elif user_data.get('waiting_for_base_hours'):
        return await handle_text_input(update, context)


# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log Errors caused by Updates."""
    error = context.error
    
    try:
        # Importa qui per evitare import circolari
        from telegram.error import RetryAfter, TimedOut, NetworkError
        
        if isinstance(error, RetryAfter):
            logger.warning(f"Rate limit: retry dopo {error.retry_after} secondi")
            return
        elif isinstance(error, TimedOut):
            logger.warning("Timeout - normale durante polling")
            return
        elif isinstance(error, NetworkError):
            logger.warning("Errore di rete temporaneo")
            return
    except:
        pass
    
    logger.warning('Update "%s" caused error "%s"', update, error)

def main():
    """Start the bot."""
    # Initialize database
    init_db()
    
    # Create the Application
    
    
    # Debug: verifica token
    token = os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))
    if not token:
        logger.error("❌ BOT TOKEN NON TROVATO!")
        logger.error("Variabili ambiente disponibili: %s", list(os.environ.keys()))
        return
    else:
        logger.info(f"✅ Token trovato: {token[:10]}...{token[-5:]}")
    
    application = Application.builder().token(
        os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))
    ).build()
    

    
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

    # Command handlers - start DEVE essere il primo!
    # Logger per debug - PRIMO handler
    application.add_handler(MessageHandler(filters.ALL, log_all_messages), group=-10)
    logger.info("📝 Message logger aggiunto")

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("nuovo", new_service_command))
    application.add_handler(CommandHandler("scorta", new_service_command))
    application.add_handler(CommandHandler("straordinari", overtime_command))
    application.add_handler(CommandHandler("fv", travel_sheets_command))
    application.add_handler(CommandHandler("licenze", leave_command))
    application.add_handler(CommandHandler("impostazioni", settings_command))
    application.add_handler(CommandHandler("oggi", today_command))
    application.add_handler(CommandHandler("mese", month_command))
    application.add_handler(CommandHandler("ieri", yesterday_command))
    application.add_handler(CommandHandler("settimana", week_command))
    application.add_handler(CommandHandler("anno", year_command))
    
    # Comando test per debug
    async def test_save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test diretto salvataggio"""
        from database.connection import SessionLocal
        from database.models import Service, ServiceType, User
        from services.calculation_service import calculate_service_total
        from datetime import datetime, date
        
        user_id = str(update.effective_user.id)
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                await update.message.reply_text("❌ Utente non trovato!")
                return
            
            # Crea servizio test
            service = Service(
                user_id=user.id,
                date=date.today(),
                start_time=datetime.now().replace(hour=9, minute=0),
                end_time=datetime.now().replace(hour=15, minute=0),
                total_hours=6.0,
                service_type=ServiceType.LOCAL,
                is_holiday=False,
                is_super_holiday=False
            )
            
            # Calcola
            calc = calculate_service_total(db, user, service)
            
            # Salva
            db.add(service)
            db.commit()
            
            # Verifica
            saved = db.query(Service).filter(Service.id == service.id).first()
            if saved:
                text = f"✅ TEST RIUSCITO!\n\n"
                text += f"Servizio salvato con ID: {saved.id}\n"
                text += f"Data: {saved.date}\n"
                text += f"Ore: {saved.total_hours}\n"
                text += f"Totale: €{saved.total_amount:.2f}"
            else:
                text = "❌ Errore: servizio non trovato dopo salvataggio!"
            
            await update.message.reply_text(text, parse_mode='HTML')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Errore: {str(e)}", parse_mode='HTML')
        finally:
            db.close()
    
    application.add_handler(CommandHandler("test", test_save_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("ore_pagate", paid_hours_command))
    application.add_handler(CommandHandler("accumulo", accumulation_command))
    application.add_handler(CommandHandler("nuova_licenza", add_leave_command))
    application.add_handler(CommandHandler("pianifica_licenze", plan_leave_command))
    application.add_handler(CommandHandler("fv_pagamento", register_payment_command))
    # CRITICAL: Conversation handlers - DEVONO essere prima dei callback generici!
    application.add_handler(service_conversation_handler)
    application.add_handler(setup_conversation_handler)
    
    # Handler per callback specifici delle licenze
    application.add_handler(CallbackQueryHandler(handle_leave_edit, pattern="^edit_(current_leave_total|current_leave_used|previous_leave)$"))
    
    # Handler per percorsi salvati
    application.add_handler(CallbackQueryHandler(handle_route_action, pattern="^(add|remove)_route$"))
    application.add_handler(CallbackQueryHandler(handle_patron_saint, pattern="^set_patron_saint$"))
    application.add_handler(CallbackQueryHandler(handle_reminder_time, pattern="^change_reminder_time$"))
    
    # Handler per selezione pasti
    application.add_handler(CallbackQueryHandler(handle_meal_selection, pattern="^meal_(lunch|dinner)$"))
    application.add_handler(CallbackQueryHandler(handle_meals, pattern="^meal_confirm$"))
    
    # Handler per tipi missione
    application.add_handler(CallbackQueryHandler(handle_mission_type, pattern="^mission_type_"))
    
    # Handler per navigazione settings
    application.add_handler(CallbackQueryHandler(update_rank, pattern="^rank_[0-9]+$"))
    application.add_handler(CallbackQueryHandler(update_irpef, pattern="^irpef_[0-9]+$"))
    
    # Handler per navigazione back
    application.add_handler(CallbackQueryHandler(handle_back_navigation, pattern="^back_"))
    
    # Handler per dashboard callbacks
    application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="^dashboard_"))
    
    # Handler per altri callback specifici
    application.add_handler(CallbackQueryHandler(overtime_callback, pattern="^overtime_"))
    application.add_handler(CallbackQueryHandler(leave_callback, pattern="^leave_"))
    application.add_handler(CallbackQueryHandler(travel_sheet_callback, pattern="^fv_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_"))
    application.add_handler(CallbackQueryHandler(rest_callback, pattern="^rest_"))
    
    # Handler per toggle notifiche
    application.add_handler(CallbackQueryHandler(toggle_notification, pattern="^toggle_"))
    
    # Comandi aggiuntivi
    
    # Handler per input testuali - DEVE essere uno degli ultimi!
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text_inputs))
    application.add_handler(CommandHandler("riposi", rest_command))

    # Debug handler rimosso - ora abbiamo handler specifici

    # Middleware pulizia chat - eseguito DOPO tutti gli handler

    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("Starting CarabinieriPayBot...")
    # # start_notification_system(application.bot)  # Disabilitato temporaneamente
    logger.info("Bot started and polling for updates...")
    # logger.info(f"Bot username: @{application.bot.username if hasattr(application.bot, 'username') else 'Unknown'}")
    
    # Avvia sistema di notifiche
    # try:
    # from services.notification_service import start_notification_system  # DISABILITATO - BLOCCAVA IL BOT
    # logger.info("Avvio sistema notifiche...")
    # start_notification_system(application.bot)  # Disabilitato temporaneamente

    # Handler per callback non gestiti - DEVE essere l'ultimo!
    async def handle_unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        logger.warning(f"Callback non implementato: {callback_data}")
        
        # Per i callback confirm_, mostra messaggio temporaneo
        if callback_data.startswith("confirm_"):
            await query.answer("⚠️ Usa i bottoni durante la registrazione del servizio", show_alert=True)
        elif "back_to_menu" in callback_data:
            await start_command(update, context)
        elif "setup_start" in callback_data:
            await query.answer("Usa /impostazioni per configurare il profilo", show_alert=True)
        else:
            await query.answer("Funzione in sviluppo", show_alert=True)
if __name__ == '__main__':
    main()
