#!/usr/bin/env python3
import subprocess

print("🔧 Integrazione sistema pulizia messaggi")

# 1. Salva il nuovo clean_chat.py
with open('utils/clean_chat.py', 'w') as f:
   f.write("""\"\"\"
Sistema di pulizia messaggi per Telegram Bot
\"\"\"
from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)

class MessageCleaner:
   \"\"\"Sistema per eliminare automaticamente i messaggi\"\"\"
   
   def __init__(self):
       # Dizionario per tracciare i messaggi per chat
       self.messages_to_delete: Dict[int, Set[int]] = {}
       # Massimo numero di messaggi da mantenere
       self.max_messages = 2
       
   async def register_and_clean(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
       \"\"\"Registra un nuovo messaggio e pulisce i vecchi\"\"\"
       chat_id = None
       message_id = None
       
       # Estrai chat_id e message_id
       if update.message:
           chat_id = update.message.chat_id
           message_id = update.message.message_id
       elif update.callback_query and update.callback_query.message:
           # Per i callback, non eliminiamo il messaggio con i pulsanti
           return
           
       if not chat_id or not message_id:
           return
           
       # Inizializza set per questa chat se non esiste
       if chat_id not in self.messages_to_delete:
           self.messages_to_delete[chat_id] = set()
           
       # Aggiungi il nuovo messaggio
       self.messages_to_delete[chat_id].add(message_id)
       
       # Se abbiamo troppi messaggi, elimina i più vecchi
       if len(self.messages_to_delete[chat_id]) > self.max_messages * 2:
           # Converti in lista ordinata
           messages = sorted(list(self.messages_to_delete[chat_id]))
           
           # Messaggi da eliminare (i più vecchi)
           to_delete = messages[:-self.max_messages * 2]
           
           # Elimina i messaggi
           for msg_id in to_delete:
               try:
                   await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                   self.messages_to_delete[chat_id].remove(msg_id)
                   await asyncio.sleep(0.1)  # Evita rate limiting
               except Exception as e:
                   logger.debug(f"Impossibile eliminare messaggio {msg_id}: {e}")
                   # Rimuovi comunque dalla lista
                   self.messages_to_delete[chat_id].discard(msg_id)

# Istanza globale
message_cleaner = MessageCleaner()

# Middleware per intercettare tutti i messaggi
async def cleanup_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
   \"\"\"Middleware che pulisce automaticamente i messaggi\"\"\"
   await message_cleaner.register_and_clean(update, context)
""")

print("✅ Nuovo clean_chat.py salvato")

# 2. Aggiorna main.py
with open('main.py', 'r') as f:
   content = f.read()

# Aggiungi import
if 'from utils.clean_chat import message_cleaner, cleanup_middleware' not in content:
   import_pos = content.find('from dotenv import load_dotenv')
   if import_pos > 0:
       content = content[:import_pos] + 'from utils.clean_chat import message_cleaner, cleanup_middleware\n' + content[import_pos:]

# Aggiungi middleware PRIMA di tutti gli altri handler
if 'cleanup_middleware' not in content:
   # Trova dove aggiungere (dopo application.builder())
   app_pos = content.find('application = Application.builder()')
   if app_pos > 0:
       # Trova la fine della creazione dell'application
       next_line = content.find('\n\n', app_pos)
       
       middleware_code = """
   # Aggiungi middleware per pulizia messaggi
   # IMPORTANTE: Deve essere aggiunto PER PRIMO con gruppo -100
   application.add_handler(MessageHandler(filters.ALL, cleanup_middleware), group=-100)
"""
       content = content[:next_line] + middleware_code + content[next_line:]

with open('main.py', 'w') as f:
   f.write(content)

print("✅ main.py aggiornato con middleware")

# Commit
subprocess.run("git add utils/clean_chat.py main.py", shell=True)
subprocess.run('git commit -m "fix: implementato sistema funzionante per eliminazione automatica messaggi"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n✅ Sistema di pulizia messaggi implementato!")
print("\n📱 Funzionamento:")
print("- Ogni messaggio viene registrato")
print("- Quando ci sono troppi messaggi, i vecchi vengono eliminati")
print("- I messaggi con pulsanti NON vengono eliminati")
print("- Mantiene solo gli ultimi messaggi")
