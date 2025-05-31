#!/usr/bin/env python3
"""Bot minimale per verificare che Railway funzioni"""
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test /start"""
    logger.info(f"Ricevuto /start da {update.effective_user.id}")
    await update.message.reply_text("✅ Il bot funziona!")

def main():
    token = os.getenv('BOT_TOKEN')
    if not token:
        logger.error("❌ BOT_TOKEN non trovato!")
        return
    
    logger.info(f"Token: {token[:10]}...{token[-5:]}")
    
    # Crea app
    app = Application.builder().token(token).build()
    
    # Aggiungi handler
    app.add_handler(CommandHandler("start", start))
    
    # Avvia
    logger.info("🚀 Avvio bot minimale...")
    app.run_polling(drop_pending_updates=True)
    logger.info("Bot terminato")  # Non dovrebbe mai arrivare qui

if __name__ == '__main__':
    main()
