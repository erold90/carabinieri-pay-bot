#!/usr/bin/env python3
"""Test di benvenuto per il bot"""
import asyncio
import os
from telegram import Bot

async def send_welcome():
    token = os.getenv('BOT_TOKEN') or os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Token non trovato")
        return
    
    print("🤖 CARABINIERI PAY BOT")
    print("=" * 40)
    print("Il bot dovrebbe essere online!")
    print()
    print("📱 VAI SU TELEGRAM E:")
    print("1. Cerca il tuo bot")
    print("2. Invia /start")
    print("3. Esplora il menu principale")
    print()
    print("🎯 COMANDI PRINCIPALI:")
    print("• /start - Menu dashboard")
    print("• /nuovo - Registra servizio")
    print("• /oggi - Riepilogo giornaliero")
    print("• /mese - Report mensile")
    print("• /straordinari - Gestione ore")
    print("• /fv - Fogli viaggio")
    print("• /impostazioni - Configurazione")
    print("=" * 40)

if __name__ == "__main__":
    asyncio.run(send_welcome())
