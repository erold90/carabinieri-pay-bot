"""
Sistema di pulizia messaggi per Telegram Bot
"""
from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import logging
from typing import Dict, Set

logger = logging.getLogger(__name__)

class MessageCleaner:
   """Sistema per eliminare automaticamente i messaggi"""
   
   def __init__(self):
       # Dizionario per tracciare i messaggi per chat
       self.messages_to_delete: Dict[int, Set[int]] = {}
       # Massimo numero di messaggi da mantenere
       self.max_messages = 2
       
   async def register_and_clean(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
       """Registra un nuovo messaggio e pulisce i vecchi"""
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
   """Middleware che pulisce automaticamente i messaggi"""
   await message_cleaner.register_and_clean(update, context)
