#!/usr/bin/env python3
"""Bot minimale per test connessione"""
import logging
import os
import asyncio
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Comando /start ricevuto da {update.effective_user.id}")
    await update.message.reply_text("✅ Bot funzionante!")

async def test_connection():
    """Test connessione bot"""
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
    if not token:
        logger.error("Token non trovato!")
        return False
    
    bot = Bot(token)
    try:
        me = await bot.get_me()
        logger.info(f"✅ Bot connesso: @{me.username}")
        await bot.close()
        return True
    except Exception as e:
        logger.error(f"❌ Errore connessione: {e}")
        return False

def main():
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN non trovato!")
        logger.error(f"Variabili disponibili: {list(os.environ.keys())}")
        return
    
    logger.info(f"Token: {token[:10]}...{token[-5:]}")
    
    # Test connessione prima
    if not asyncio.run(test_connection()):
        logger.error("Test connessione fallito!")
        return
    
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    
    logger.info("Avvio polling...")
    try:
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        logger.error(f"Errore: {e}")

if __name__ == '__main__':
    main()
