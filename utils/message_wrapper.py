"""
Wrapper per aggiungere pulizia automatica agli handler
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from utils.clean_chat import register_user_message, register_bot_message

def with_message_cleanup(func):
    """Decorator che aggiunge pulizia automatica messaggi"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Registra messaggio utente
        if update.message:
            await register_user_message(update, context)
        
        # Esegui handler originale
        result = await func(update, context)
        
        # Se l'handler ha restituito un messaggio, registralo
        if result and hasattr(result, 'message_id'):
            await register_bot_message(result, context)
            
        return result
    
    return wrapper
