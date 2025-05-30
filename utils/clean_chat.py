"""
Sistema di pulizia automatica messaggi per CarabinieriPayBot
"""
from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import logging
from typing import Dict, List
from collections import deque

logger = logging.getLogger(__name__)

class MessageCleaner:
    """Gestisce l'eliminazione automatica dei messaggi"""
    
    def __init__(self):
        # Mantieni una coda di messaggi per chat_id
        self.message_history: Dict[int, deque] = {}
        # Numero massimo di messaggi da mantenere
        self.max_messages = 1
        # Messaggi da non eliminare (con pulsanti)
        self.protected_messages: Dict[int, set] = {}
        
    async def add_message(self, chat_id: int, message_id: int, context: ContextTypes.DEFAULT_TYPE, is_protected: bool = False):
        """Aggiunge un messaggio e pulisce i vecchi"""
        
        # Inizializza la coda per questa chat se non esiste
        if chat_id not in self.message_history:
            self.message_history[chat_id] = deque(maxlen=self.max_messages * 2)
            self.protected_messages[chat_id] = set()
        
        # Aggiungi il messaggio
        self.message_history[chat_id].append(message_id)
        
        # Se è protetto (con pulsanti), segnalo
        if is_protected:
            self.protected_messages[chat_id].add(message_id)
        
        # Pulisci i messaggi vecchi
        await self._cleanup_old_messages(chat_id, context)
    
    async def _cleanup_old_messages(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Elimina i messaggi vecchi mantenendo solo gli ultimi"""
        
        messages = list(self.message_history[chat_id])
        
        # Se abbiamo troppi messaggi
        if len(messages) > self.max_messages:
            # Messaggi da eliminare (i più vecchi)
            to_delete = messages[:-self.max_messages]
            
            for msg_id in to_delete:
                # Non eliminare messaggi protetti
                if msg_id in self.protected_messages.get(chat_id, set()):
                    continue
                    
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    # Rimuovi dalla history
                    if msg_id in self.message_history[chat_id]:
                        self.message_history[chat_id].remove(msg_id)
                    await asyncio.sleep(0.1)  # Anti rate-limit
                except Exception as e:
                    logger.debug(f"Non posso eliminare {msg_id}: {e}")

# Istanza globale
cleaner = MessageCleaner()

async def register_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registra un messaggio utente per la pulizia"""
    if update.message:
        await cleaner.add_message(
            update.message.chat_id,
            update.message.message_id,
            context,
            is_protected=False
        )

async def register_bot_message(message, context: ContextTypes.DEFAULT_TYPE):
    """Registra un messaggio del bot"""
    if message:
        # Controlla se ha pulsanti inline
        has_buttons = bool(message.reply_markup)
        await cleaner.add_message(
            message.chat_id,
            message.message_id,
            context,
            is_protected=has_buttons
        )

# Middleware per intercettare tutti i messaggi
async def cleanup_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Middleware che registra automaticamente i messaggi"""
    if update.message:
        await register_user_message(update, context)

async def delete_message_after_delay(message, delay=3):
    """Elimina un messaggio dopo un delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass


# Sistema semplificato di auto-delete
AUTO_DELETE_ENABLED = True
DELETE_DELAY = 30  # secondi

async def setup_auto_delete(application):
    """Setup auto-delete per l'applicazione"""
    print("✅ Sistema auto-delete configurato")

