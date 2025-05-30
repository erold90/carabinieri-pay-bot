#!/usr/bin/env python3
import asyncio
from telegram import Bot
from telegram.error import TelegramError
import os

async def test_bot():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ BOT_TOKEN non trovato nelle variabili d'ambiente")
        return
        
    bot = Bot(token)
    
    try:
        me = await bot.get_me()
        print(f"✅ Bot online: @{me.username}")
        print(f"   Nome: {me.first_name}")
        print(f"   ID: {me.id}")
        
        # Test comandi
        commands = await bot.get_my_commands()
        if commands:
            print("\n📋 Comandi registrati:")
            for cmd in commands:
                print(f"   /{cmd.command} - {cmd.description}")
        
    except TelegramError as e:
        print(f"❌ Errore connessione bot: {e}")

if __name__ == "__main__":
    print("🤖 TEST CONNESSIONE BOT\n")
    asyncio.run(test_bot())
