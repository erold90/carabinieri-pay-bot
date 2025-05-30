#!/usr/bin/env python3
"""
Wrapper per aggiungere clean chat a tutti gli handler
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from utils.clean_chat import chat_cleaner

def clean_chat_command(func):
    """Decorator per command handler con pulizia chat"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Registra il messaggio dell'utente per l'eliminazione
        if update.message:
            await chat_cleaner.register_user_message(update.message, context)
        
        # Esegui l'handler
        result = await func(update, context)
        
        return result
    
    return wrapper

def clean_chat_callback(func):
    """Decorator per callback handler"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Per i callback non serve eliminare, si editano
        result = await func(update, context)
        return result
    
    return wrapper
