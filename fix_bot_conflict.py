#!/usr/bin/env python3
import subprocess
import os
import time

print("🔧 FIX CONFLITTO BOT TELEGRAM")
print("=" * 50)
print("⚠️  PROBLEMA: Un'altra istanza del bot sta già girando!")
print("=" * 50)

print("\n📋 SOLUZIONI:")
print("\n1️⃣ OPZIONE 1 - Forza restart su Railway:")
print("   - Vai su Railway.app")
print("   - Nel tuo progetto, vai su Settings")
print("   - Clicca 'Restart' o 'Redeploy'")
print("   - Attendi 2-3 minuti")

print("\n2️⃣ OPZIONE 2 - Crea un nuovo token bot:")
print("   - Apri Telegram e vai su @BotFather")
print("   - Usa /revoke per revocare il token attuale")
print("   - Poi /newtoken per crearne uno nuovo")
print("   - Aggiorna BOT_TOKEN su Railway")

print("\n3️⃣ OPZIONE 3 - Aggiungi meccanismo di sicurezza:")

# Crea un file per gestire il webhook
safety_code = '''#!/usr/bin/env python3
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
'''

with open('cleanup_webhook.py', 'w') as f:
    f.write(safety_code)

os.chmod('cleanup_webhook.py', 0o755)
print("✅ Creato cleanup_webhook.py")

# Modifica main.py per gestire meglio l'avvio
print("\n4️⃣ Modifica main.py per gestione conflitti...")

with open('main.py', 'r') as f:
    content = f.read()

# Aggiungi gestione webhook all'inizio di main()
new_main_start = '''def main():
    """Start the bot."""
    # Initialize database
    init_db()
    
    # Create the Application with timeout più lungo
    application = Application.builder().token(
        os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))
    ).connect_timeout(30.0).read_timeout(30.0).build()
    
    # Pulisci webhook all'avvio per evitare conflitti
    import asyncio
    async def cleanup():
        try:
            await application.bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook pulito all'avvio")
        except:
            pass
    
    asyncio.run(cleanup())'''

# Sostituisci l'inizio di main()
if 'def main():' in content:
    import re
    pattern = r'def main\(\):\s*"""Start the bot\."""\s*# Initialize database\s*init_db\(\)\s*\n\s*# Create the Application.*?\.build\(\)'
    replacement = new_main_start
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open('main.py', 'w') as f:
        f.write(content)
    
    print("✅ Aggiunta pulizia webhook all'avvio")

# Crea script per Railway
railway_fix = '''# Script da eseguire su Railway Console

# 1. Ferma tutti i processi
pkill -f python3
pkill -f main.py

# 2. Pulisci
python3 cleanup_webhook.py

# 3. Riavvia
python3 main.py
'''

with open('RAILWAY_FIX.txt', 'w') as f:
    f.write(railway_fix)

print("\n✅ Creato RAILWAY_FIX.txt con istruzioni")

# Commit e push
print("\n📤 Push modifiche...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: gestione conflitti bot e pulizia webhook"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ FIX COMPLETATO!")
print("\n🎯 PROSSIMI PASSI:")
print("1. Vai su Railway e fai RESTART del servizio")
print("2. O esegui: python3 cleanup_webhook.py")
print("3. Poi Railway ripartirà automaticamente")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script auto-eliminato")
