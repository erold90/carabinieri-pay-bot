#!/usr/bin/env python3
"""Script di monitoraggio bot"""
import asyncio
import os
from telegram import Bot
from database.connection import test_connection
from datetime import datetime

async def monitor_bot():
    """Monitora stato del bot"""
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ Token non trovato")
        return
    
    bot = Bot(token)
    
    print(f"🔍 MONITORAGGIO BOT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test bot
    try:
        me = await bot.get_me()
        print(f"✅ Bot online: @{me.username}")
        
        # Controlla webhook
        webhook = await bot.get_webhook_info()
        if webhook.url:
            print(f"⚠️  Webhook attivo: {webhook.url}")
        else:
            print("✅ Polling attivo")
            
    except Exception as e:
        print(f"❌ Bot offline: {e}")
    
    # Test database
    if test_connection():
        print("✅ Database connesso")
    else:
        print("❌ Database non connesso")
    
    await bot.close()

if __name__ == "__main__":
    asyncio.run(monitor_bot())
