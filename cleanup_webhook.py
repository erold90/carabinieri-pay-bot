#!/usr/bin/env python3
"""Script per forzare pulizia webhook"""
import asyncio
from telegram import Bot
import os

async def force_cleanup():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ BOT_TOKEN non trovato!")
        return
    
    bot = Bot(token)
    
    try:
        # Elimina webhook se esiste
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook eliminato")
        
        # Info bot
        me = await bot.get_me()
        print(f"🤖 Bot: @{me.username}")
        
        # Chiudi tutto
        await bot.close()
        print("✅ Bot chiuso correttamente")
        
    except Exception as e:
        print(f"❌ Errore: {e}")

if __name__ == "__main__":
    print("🧹 PULIZIA WEBHOOK BOT")
    print("=" * 50)
    asyncio.run(force_cleanup())
