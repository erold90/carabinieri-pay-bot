"""
Clean Chat Handler - Sistema migliorato
"""
from telegram import Update, Message
from telegram.ext import ContextTypes
import logging
from typing import Dict, List
import asyncio

logger = logging.getLogger(__name__)

class ChatCleaner:
    """Gestore per mantenere la chat pulita"""
    
    def __init__(self):
        self.message_history: Dict[int, List[int]] = {}
        self.max_messages = 3
    
    async def add_message(self, chat_id: int, message_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Aggiunge un messaggio alla cronologia e pulisce i vecchi"""
        if chat_id not in self.message_history:
            self.message_history[chat_id] = []
        
        self.message_history[chat_id].append(message_id)
        
        # Elimina messaggi vecchi se necessario
        if len(self.message_history[chat_id]) > self.max_messages:
            old_messages = self.message_history[chat_id][:-self.max_messages]
            self.message_history[chat_id] = self.message_history[chat_id][-self.max_messages:]
            
            for msg_id in old_messages:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    await asyncio.sleep(0.1)
                except Exception as e:
                    logger.debug(f"Cannot delete message {msg_id}: {e}")
    
    async def clean_all(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Elimina tutti i messaggi della chat"""
        if chat_id in self.message_history:
            for msg_id in self.message_history[chat_id]:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    await asyncio.sleep(0.1)
                except:
                    pass
            self.message_history[chat_id] = []

# Istanza globale
chat_cleaner = ChatCleaner()

async def register_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registra un messaggio per la pulizia"""
    if update.message:
        await chat_cleaner.add_message(
            update.message.chat_id,
            update.message.message_id,
            context
        )
