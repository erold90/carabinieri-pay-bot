"""
Clean Chat Handler - Mantiene solo l'ultimo messaggio
"""
from telegram import Update, Message, CallbackQuery
from telegram.ext import ContextTypes
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ChatCleaner:
    """Gestore per mantenere la chat pulita con solo l'ultimo messaggio"""
    
    def __init__(self):
        self.user_last_messages = {}  # {chat_id: message_id}
        self.bot_last_messages = {}   # {chat_id: message_id}
    
    async def clean_previous_messages(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Elimina tutti i messaggi precedenti"""
        messages_to_delete = []
        
        # Raccogli i message_id da eliminare
        if chat_id in self.user_last_messages:
            messages_to_delete.append(self.user_last_messages[chat_id])
        
        if chat_id in self.bot_last_messages:
            messages_to_delete.append(self.bot_last_messages[chat_id])
        
        # Elimina i messaggi
        for msg_id in messages_to_delete:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.debug(f"Impossibile eliminare messaggio {msg_id}: {e}")
        
        # Pulisci i riferimenti
        self.user_last_messages.pop(chat_id, None)
        self.bot_last_messages.pop(chat_id, None)
    
    async def register_user_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE):
        """Registra un messaggio dell'utente e pulisce i precedenti"""
        chat_id = message.chat_id
        
        # Pulisci i messaggi precedenti
        await self.clean_previous_messages(chat_id, context)
        
        # Registra il nuovo messaggio
        self.user_last_messages[chat_id] = message.message_id
    
    async def register_bot_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE):
        """Registra un messaggio del bot"""
        chat_id = message.chat_id
        
        # Elimina solo il messaggio dell'utente, non il precedente del bot
        # (perché potrebbe essere un edit)
        if chat_id in self.user_last_messages:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id, 
                    message_id=self.user_last_messages[chat_id]
                )
            except:
                pass
            del self.user_last_messages[chat_id]
        
        # Registra il nuovo messaggio del bot
        self.bot_last_messages[chat_id] = message.message_id
    
    async def handle_callback_query(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce i callback query (pulsanti inline)"""
        # Quando viene premuto un pulsante, il messaggio viene editato
        # quindi non serve eliminarlo, è già gestito
        pass

# Istanza globale del cleaner
chat_cleaner = ChatCleaner()

async def wrap_handler_with_cleanup(handler_func):
    """Decorator per aggiungere la pulizia automatica agli handler"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Se è un messaggio normale
        if update.message:
            await chat_cleaner.register_user_message(update.message, context)
        
        # Esegui l'handler originale
        result = await handler_func(update, context)
        
        # Se l'handler ha restituito un messaggio, registralo
        if isinstance(result, Message):
            await chat_cleaner.register_bot_message(result, context)
        
        return result
    
    return wrapper

async def clean_chat_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE, next_handler):
    """Middleware per gestire la pulizia della chat"""
    # Per i messaggi
    if update.message:
        await chat_cleaner.register_user_message(update.message, context)
    
    # Esegui il prossimo handler
    result = await next_handler(update, context)
    
    return result

# Funzioni helper per gli handler esistenti
async def send_and_clean(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs):
    """Invia un messaggio e registralo per la pulizia"""
    if update.callback_query:
        # Se è un callback, edita il messaggio esistente
        message = await update.callback_query.edit_message_text(text, **kwargs)
    else:
        # Altrimenti invia un nuovo messaggio
        message = await update.effective_message.reply_text(text, **kwargs)
        if message:
            await chat_cleaner.register_bot_message(message, context)
    
    return message

async def delete_after_delay(message: Message, delay: int = 5):
    """Elimina un messaggio dopo un delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass
