#!/usr/bin/env python3
"""Monitora l'avvio del bot in tempo reale"""
import asyncio
import os
from datetime import datetime
from telegram import Bot
import time

async def test_bot_response():
    """Testa se il bot risponde"""
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ BOT_TOKEN non trovato!")
        return False
    
    bot = Bot(token)
    try:
        # Info bot
        me = await bot.get_me()
        print(f"\n✅ Bot trovato: @{me.username}")
        print(f"🔗 Link: https://t.me/{me.username}")
        
        # Controlla webhook
        webhook = await bot.get_webhook_info()
        if webhook.url:
            print(f"⚠️ Webhook ancora attivo: {webhook.url}")
            print("  Rimuovendolo...")
            await bot.delete_webhook(drop_pending_updates=True)
            await asyncio.sleep(2)
            print("✅ Webhook rimosso!")
        
        # Controlla messaggi in coda
        print("\n📨 Controllo messaggi...")
        updates = await bot.get_updates(limit=10, timeout=2)
        
        if updates:
            print(f"📬 {len(updates)} messaggi in coda:")
            for u in updates[-5:]:  # Ultimi 5
                if u.message and u.message.text:
                    user = u.message.from_user.username or u.message.from_user.first_name
                    print(f"  • {u.message.text} (da @{user})")
                    
                    # Se c'è /start, il bot dovrebbe aver risposto
                    if u.message.text == '/start':
                        print("    ⚠️ Il bot ha ricevuto /start ma potrebbe non aver risposto")
        else:
            print("📭 Nessun messaggio in attesa")
        
        return True
        
    except Exception as e:
        print(f"⏳ Bot non ancora pronto: {str(e)[:50]}...")
        return False
    finally:
        await bot.close()

async def send_test_command():
    """Invia comando di test"""
    print("\n" + "="*60)
    print("🧪 TEST MANUALE:")
    print("1. Apri Telegram")
    print("2. Cerca il tuo bot")
    print("3. Invia questi comandi:")
    print("   /start - Menu principale")
    print("   /hello - Test semplice")
    print("   /ping  - Risposta veloce")
    print("\n📱 Controlla se ricevi risposta!")
    print("="*60)

async def main():
    print("🔍 MONITORAGGIO AVVIO BOT")
    print("="*80)
    start_time = time.time()
    
    # Test iniziale
    print("\n🚀 Controllo iniziale...")
    if await test_bot_response():
        print("\n✅ Il bot è già online!")
        await send_test_command()
        return
    
    # Monitoring loop
    print("\n⏳ Attendo che il bot si avvii...")
    print("   (Controllo ogni 10 secondi)")
    
    attempts = 0
    max_attempts = 30  # 5 minuti
    
    while attempts < max_attempts:
        attempts += 1
        await asyncio.sleep(10)
        
        print(f"\n🔄 Tentativo {attempts}/{max_attempts} - {datetime.now().strftime('%H:%M:%S')}")
        
        if await test_bot_response():
            elapsed = int(time.time() - start_time)
            print(f"\n{'🎉'*20}")
            print(f"✅ BOT ONLINE! (Tempo: {elapsed} secondi)")
            print(f"{'🎉'*20}")
            
            await send_test_command()
            
            # Test finale con countdown
            print("\n⏰ Test automatico tra 5 secondi...")
            for i in range(5, 0, -1):
                print(f"   {i}...")
                await asyncio.sleep(1)
            
            # Verifica finale
            print("\n🔍 Verifica finale...")
            await test_bot_response()
            
            break
    
    if attempts >= max_attempts:
        print("\n❌ TIMEOUT!")
        print("\n🔧 Possibili soluzioni:")
        print("1. Controlla i log su Railway per errori")
        print("2. Verifica che BOT_TOKEN sia configurato")
        print("3. Prova: python3 cleanup_webhook.py")
        print("4. Riavvia il deployment su Railway")

if __name__ == "__main__":
    asyncio.run(main())
    
    # Crea script di cleanup se necessario
    cleanup_script = '''#!/usr/bin/env python3
import asyncio
from telegram import Bot
import os

async def force_cleanup():
    token = os.getenv('BOT_TOKEN')
    if not token:
        print("❌ Token non trovato!")
        return
    
    bot = Bot(token)
    try:
        # Forza rimozione webhook
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook rimosso forzatamente")
        
        # Pulisci update pendenti
        updates = await bot.get_updates(offset=-1)
        print(f"✅ Puliti {len(updates)} messaggi pendenti")
        
        # Info
        me = await bot.get_me()
        print(f"✅ Bot: @{me.username} pronto per polling")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    print("🧹 PULIZIA FORZATA BOT")
    print("="*50)
    asyncio.run(force_cleanup())
'''
    
    with open('force_cleanup.py', 'w') as f:
        f.write(cleanup_script)
    os.chmod('force_cleanup.py', 0o755)
    print("\n💡 Creato force_cleanup.py per pulizia forzata se necessario")
    
    # Auto-elimina
    os.remove(__file__)
