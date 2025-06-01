# import asyncio
# import gc
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
from utils.logging_config import setup_logging, log_info, log_success, log_error, log_warning
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
    handle_meal_selection,
    handle_confirmation,
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
from handlers.service_handler import new_service_command
from handlers.leave_handler import leave_command, add_leave_command, plan_leave_command

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()


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
        # logger\.info\(f"📨 MESSAGGIO RICEVUTO:.*?
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
    
    # Ignora errori comuni non critici
    if isinstance(error, (RetryAfter, TimedOut, NetworkError)):
        logger.debug(f"Errore di rete temporaneo: {error}")
        return
    
    # Log dettagliato per altri errori
    logger.error(f"Errore in update {update}: {error}", exc_info=True)
    
    # Notifica utente se possibile
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Si è verificato un errore. Riprova o usa /start",
                parse_mode='HTML'
            )
    except:
        pass


# Aggiungi questo handler di test in main.py
async def hello_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("✅ COMANDO /hello ricevuto")
    """Comando test semplice"""
    try:
        logger.info("HELLO COMMAND CHIAMATO")
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        chat_id = update.effective_chat.id if update.effective_chat else "Unknown"
        username = update.effective_user.username if update.effective_user else "Unknown"
        
        message = (
            "👋 Ciao! Il bot funziona!\n\n"
            "Debug info:\n"
            f"User ID: {user_id}\n"
            f"Chat ID: {chat_id}\n"
            f"Username: @{username}"
        )
        
        await update.message.reply_text(message)
        logger.info("Hello command completato con successo")
    except Exception as e:
        logger.error(f"Errore in hello_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Errore nel comando hello")


async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando ping super semplice"""
    await update.message.reply_text("🏓 Pong!")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostra stato del bot"""
    from database.connection import test_connection
    
    db_status = "✅ Connesso" if test_connection() else "❌ Non connesso"
    
    message = (
        "🤖 <b>STATO BOT</b>\n\n"
        f"Bot: ✅ Online\n"
        f"Database: {db_status}\n"
        f"Versione: 3.0\n"
        f"Ambiente: {os.getenv('ENV', 'development')}\n\n"
        "Comandi disponibili:\n"
        "/ping - Test veloce\n"
        "/hello - Info debug\n"
        "/start - Menu principale\n"
        "/status - Questo comando"
    )
    
    await update.message.reply_text(message, parse_mode='HTML')


# Job per garbage collection periodico
def periodic_gc(context):
    """Garbage collection periodico"""
    pass


async def cleanup_webhook_on_start(application):
    """Rimuove webhook all'avvio per garantire polling pulito"""
    try:
        await application.bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook rimosso, polling mode attivo")
        
        # Verifica che non ci siano webhook
        webhook_info = await application.bot.get_webhook_info()
        if webhook_info.url:
            log_warning(f" Webhook ancora presente: {webhook_info.url}")
        else:
            logger.info("✅ Nessun webhook attivo")
            
    except Exception as e:
        logger.error(f"Errore rimozione webhook: {e}")



async def start_bot(application):
    """Avvia il bot con gestione asincrona corretta"""
    # Cleanup webhook prima di iniziare
    logger.info("🚀 Avvio CarabinieriPayBot...")
    
    # Inizializza e pulisci webhook
    await application.initialize()
    await cleanup_webhook_on_start(application)
    
    # Avvia bot info
    try:
        bot_info = await application.bot.get_me()
        logger.info(f"✅ Bot: @{bot_info.username} (ID: {bot_info.id})")
    except Exception as e:
        log_error(f"Errore info bot: {e}")
    
    # Start polling con parametri ottimizzati
    logger.info("📡 Avvio polling...")
    application.add_handler(CommandHandler("licenze", leave_command))
    application.add_handler(CommandHandler("nuova_licenza", add_leave_command))
    application.add_handler(CommandHandler("pianifica_licenze", plan_leave_command))
    await application.start()
    await application.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30,
        pool_timeout=30
    )
    
    log_success("Bot avviato e in ascolto!")
    logger.info("📱 Invia /start al bot per testare")
    
    # Mantieni il bot in esecuzione
    await application.updater.idle()


# Aggiungi logging per ogni update ricevuto
async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log ogni update per debug"""
    if update.message:
        logger.debug(f"📨 Message update: {update.message.text} from {update.effective_user.id}")
    elif update.callback_query:
        logger.debug(f"🔘 Callback update: {update.callback_query.data}")
    elif update.edited_message:
        logger.debug(f"✏️ Edited message update")
    else:
        logger.debug(f"❓ Other update type: {update}")

async def debug_middleware(update, context):
    """Log tutto per debug"""
    logger.info(f"🆕 Update ricevuto: {update}")
    if update.message:
        logger.info(f"   Messaggio: {update.message.text}")
        logger.info(f"   Da: {update.effective_user.username}")


def main():
    """Start the bot."""
    # Initialize database
    try:
        if init_db():
            logger.info("✅ Database inizializzato")
        else:
            logger.warning("⚠️ Database non disponibile, modalità limitata")
    except Exception as e:
        logger.error(f"Errore init database: {e}")
        logger.warning("Il bot continuerà senza database")
    
    # Create the Application
    token = os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))
    if not token:
        logger.error("❌ BOT TOKEN NON TROVATO!")
        logger.error("Variabili ambiente disponibili: %s", list(os.environ.keys()))
        return
    else:
        logger.info(f"✅ Token trovato: {token[:10]}...{token[-5:]}")
    
    application = Application.builder().token(token).build()

    # Aggiungi job periodici (se disponibile)
    if application.job_queue:
        job_queue = application.job_queue
        job_queue.run_repeating(periodic_gc, interval=1800, first=600)
        logger.info("✅ Job Queue configurato")
    else:
        logger.warning("⚠️ Job Queue non disponibile")
    
    # Logger per debug - PRIMO handler
    application.add_handler(MessageHandler(filters.ALL, log_all_messages), group=-10)
    logger.info("📝 Message logger aggiunto")

    # Logging handler per debug
    application.add_handler(MessageHandler(filters.ALL, log_update), group=-10)
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("hello", hello_command))
    application.add_handler(CommandHandler("ping", ping_command))
    application.add_handler(CommandHandler("status", status_command))
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
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("ore_pagate", paid_hours_command))
    application.add_handler(CommandHandler("accumulo", accumulation_command))
    application.add_handler(CommandHandler("nuova_licenza", add_leave_command))
    application.add_handler(CommandHandler("pianifica_licenze", plan_leave_command))
    application.add_handler(CommandHandler("fv_pagamento", register_payment_command))
    application.add_handler(CommandHandler("riposi", rest_command))
    
    # Conversation handlers
    application.add_handler(service_conversation_handler)
    application.add_handler(setup_conversation_handler)
    
    # Callback handlers specifici
    application.add_handler(CallbackQueryHandler(handle_leave_edit, pattern="^edit_(current_leave_total|current_leave_used|previous_leave)$"))
    application.add_handler(CallbackQueryHandler(handle_route_action, pattern="^(add|remove)_route$"))
    application.add_handler(CallbackQueryHandler(handle_patron_saint, pattern="^set_patron_saint$"))
    application.add_handler(CallbackQueryHandler(handle_reminder_time, pattern="^change_reminder_time$"))
    application.add_handler(CallbackQueryHandler(handle_meal_selection, pattern="^meal_(lunch|dinner)$"))
    application.add_handler(CallbackQueryHandler(handle_meals, pattern="^meal_confirm$"))
    application.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^confirm_"))
    application.add_handler(CallbackQueryHandler(handle_mission_type, pattern="^mission_type_"))
    application.add_handler(CallbackQueryHandler(update_rank, pattern="^rank_[0-9]+$"))
    application.add_handler(CallbackQueryHandler(update_irpef, pattern="^irpef_[0-9]+$"))
    application.add_handler(CallbackQueryHandler(handle_back_navigation, pattern="^back_"))
    application.add_handler(CallbackQueryHandler(dashboard_callback, pattern="^dashboard_"))
    # Handler per conferme
    application.add_handler(CallbackQueryHandler(overtime_callback, pattern="^overtime_"))
    application.add_handler(CallbackQueryHandler(leave_callback, pattern="^leave_"))
    application.add_handler(CallbackQueryHandler(travel_sheet_callback, pattern="^fv_"))
    application.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings_"))
    application.add_handler(CallbackQueryHandler(rest_callback, pattern="^rest_"))
    application.add_handler(CallbackQueryHandler(toggle_notification, pattern="^toggle_"))
    
    # Handler per input testuali
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text_inputs))
    
    # Catch-all per callback non gestiti
    application.add_handler(CallbackQueryHandler(debug_unhandled_callback))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    log_info("Avvio CarabinieriPayBot...")
    
    # Run polling senza asyncio
    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=None
    )



if __name__ == '__main__':
    import sys
    
    # Setup logging
    logger = setup_logging()
    
    # Load environment
    load_dotenv()
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot fermato dall'utente")
    except Exception as e:
        print(f"❌ Errore critico: {e}")
        import traceback
        traceback.print_exc()
