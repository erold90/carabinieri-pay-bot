#!/usr/bin/env python3
"""Script di cleanup per Railway"""
import asyncio
import os
from telegram import Bot

async def cleanup():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("Token non trovato")
        return
        
    bot = Bot(token)
    try:
        # Rimuovi webhook se presente
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook rimosso")
        
        # Non chiamare close() per evitare rate limit
        # await bot.close()
        
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    asyncio.run(cleanup())
