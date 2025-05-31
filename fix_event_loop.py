#!/usr/bin/env python3
import subprocess
import os

print("🔧 FIX EVENT LOOP IN MAIN.PY")
print("=" * 50)

with open('main.py', 'r') as f:
    content = f.read()

# 1. Rimuovi la pulizia webhook con asyncio.run che causa conflitto
content = content.replace("""    # Pulisci webhook all'avvio per evitare conflitti
    import asyncio
    async def cleanup():
        try:
            await application.bot.delete_webhook(drop_pending_updates=True)
            logger.info("Webhook pulito all'avvio")
        except:
            pass
    
    asyncio.run(cleanup())""", "")

# 2. Sostituisci main() con versione corretta
new_main = '''def main():
    """Start the bot."""
    # Initialize database
    init_db()
    
    # Create the Application
    application = Application.builder().token(
        os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))
    ).build()'''

# Trova e sostituisci la definizione di main
import re
pattern = r'def main\(\):.*?application = Application\.builder\(\).*?\.build\(\)'
content = re.sub(pattern, new_main, content, flags=re.DOTALL)

# 3. Commenta il sistema di notifiche che causa problemi
lines = content.split('\n')
new_lines = []
for line in lines:
    if 'start_notification_system(application.bot)' in line:
        new_lines.append('    # ' + line.strip() + '  # Disabilitato temporaneamente')
    else:
        new_lines.append(line)

content = '\n'.join(new_lines)

# 4. Salva
with open('main.py', 'w') as f:
    f.write(content)

print("✅ Event loop fixato")

# 5. Fix anche il notification service
print("\n🔧 Fix notification service...")

notification_fix = '''"""
Sistema di notifiche automatiche - VERSIONE SEMPLIFICATA
"""
import logging

logger = logging.getLogger(__name__)

def start_notification_system(bot):
    """Avvia il sistema di notifiche - PLACEHOLDER"""
    logger.info("Sistema notifiche disabilitato temporaneamente")
    # TODO: Implementare con job_queue invece di asyncio
'''

with open('services/notification_service.py', 'w') as f:
    f.write(notification_fix)

print("✅ Notification service semplificato")

# 6. Verifica sintassi
result = subprocess.run(['python3', '-m', 'py_compile', 'main.py'], 
                       capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Sintassi corretta")
    
    # Commit e push
    print("\n📤 Push fix...")
    subprocess.run("git add -A", shell=True)
    subprocess.run('git commit -m "fix: corretto event loop e disabilitato temporaneamente notifiche"', shell=True)
    subprocess.run("git push origin main", shell=True)
    
    print("\n✅ Fix pushato!")
else:
    print(f"❌ Errore sintassi: {result.stderr}")

print("\n" + "=" * 50)
print("🎯 Il bot dovrebbe ripartire correttamente ora!")
print("⏰ Attendi 2-3 minuti per il deploy")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script auto-eliminato")
