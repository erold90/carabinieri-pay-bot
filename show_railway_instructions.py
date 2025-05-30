#!/usr/bin/env python3
print("""
🚂 CONFIGURAZIONE VARIABILI RAILWAY (via Browser)
================================================

1. Vai su https://railway.app/dashboard

2. Seleziona il progetto 'CarabinieriPayBot'

3. Clicca sulla scheda 'Variables'

4. Aggiungi queste variabili:

   BOT_TOKEN = [il token del tuo bot da @BotFather]
   TZ = Europe/Rome
   ENV = production

5. DATABASE_URL dovrebbe essere già configurato automaticamente

6. Clicca 'Save' o 'Deploy' 

7. Railway farà il redeploy automaticamente

================================================

📊 Per monitorare il deploy:
railway logs --tail

🤖 Per ottenere il BOT_TOKEN:
1. Apri Telegram
2. Cerca @BotFather
3. Invia /mybots
4. Seleziona il tuo bot
5. Clicca 'API Token'
6. Copia il token (formato: 1234567890:ABCdefGHIjklMNOpqrsTUVwxyz)
""")
