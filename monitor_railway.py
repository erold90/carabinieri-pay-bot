#!/usr/bin/env python3
"""Monitora il bot su Railway"""
import os
import time
import asyncio
from telegram import Bot

async def monitor():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ Token non trovato")
        return
    
    bot = Bot(token)
    print("🔍 Monitoraggio bot...")
    
    for i in range(5):
        try:
            updates = await bot.get_updates(timeout=5)
            print(f"\n📨 Update {i+1}: {len(updates)} messaggi")
            
            for update in updates[-5:]:  # Ultimi 5
                if update.message:
                    print(f"  - {update.message.text} da {update.message.from_user.username}")
            
            webhook = await bot.get_webhook_info()
            print(f"🌐 Webhook: {'ATTIVO' if webhook.url else 'NON ATTIVO'}")
            
            if webhook.url:
                print(f"   URL: {webhook.url}")
                
        except Exception as e:
            print(f"❌ Errore: {e}")
        
        time.sleep(2)
    
    await bot.close()

asyncio.run(monitor())
