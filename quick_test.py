#!/usr/bin/env python3
"""Test veloce del bot"""
import os
import asyncio
from telegram import Bot

async def test_bot():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ Token non trovato!")
        return
    
    bot = Bot(token)
    try:
        me = await bot.get_me()
        print(f"✅ Bot online: @{me.username}")
        
        # Elimina webhook se presente
        webhook = await bot.get_webhook_info()
        if webhook.url:
            print("⚠️ Webhook attivo, lo rimuovo...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook rimosso")
        
        print("\n📱 Ora prova a inviare /start al bot!")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(test_bot())
