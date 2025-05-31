#!/usr/bin/env python3
"""Verifica configurazione bot"""
import os
import asyncio
from telegram import Bot

async def verify_bot():
    token = os.getenv('TELEGRAM_BOT_TOKEN') or os.getenv('BOT_TOKEN')
    
    print("🔍 VERIFICA CONFIGURAZIONE BOT")
    print("=" * 50)
    
    if not token:
        print("❌ TOKEN NON TROVATO!")
        print("Variabili ambiente:")
        for key in sorted(os.environ.keys()):
            if 'TOKEN' in key or 'BOT' in key:
                print(f"  {key}: {os.environ[key][:20]}...")
        return
    
    print(f"✅ Token trovato: {token[:20]}...{token[-10:]}")
    print(f"   Lunghezza: {len(token)} caratteri")
    
    bot = Bot(token)
    try:
        me = await bot.get_me()
        print(f"✅ Bot valido: @{me.username}")
        print(f"   Nome: {me.first_name}")
        print(f"   ID: {me.id}")
        
        # Prova a eliminare webhook se presente
        webhook = await bot.get_webhook_info()
        if webhook.url:
            print(f"⚠️  Webhook attivo: {webhook.url}")
            print("   Rimozione webhook...")
            await bot.delete_webhook(drop_pending_updates=True)
            print("✅ Webhook rimosso")
        else:
            print("✅ Nessun webhook attivo")
            
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    asyncio.run(verify_bot())
