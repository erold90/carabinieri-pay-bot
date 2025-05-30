#!/usr/bin/env python3
"""
Debug handler per verificare tutti i callback e database operations
"""
from telegram import Update
from telegram.ext import ContextTypes
from database.connection import SessionLocal
from database.models import User
import json

async def debug_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler universale per debug di tutti i callback"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = str(query.from_user.id)
    
    print(f"[DEBUG] Callback ricevuto: {callback_data} da user {user_id}")
    
    # Log nel database per verificare
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if user:
            print(f"[DEBUG] User trovato: {user.first_name} (ID: {user.id})")
            print(f"[DEBUG] Grado: {user.rank}, Comando: {user.command}")
            print(f"[DEBUG] IRPEF: {user.irpef_rate}, Turno base: {user.base_shift_hours}")
        else:
            print(f"[DEBUG] User non trovato nel DB!")
    finally:
        db.close()
    
    # Messaggio di debug all'utente
    debug_msg = f"⚠️ Callback non gestito: <code>{callback_data}</code>\n"
    debug_msg += "Questo pulsante non ha ancora un handler associato."
    
    await query.edit_message_text(debug_msg, parse_mode='HTML')

async def verify_database_write(user_id: str, field: str, value: any):
    """Verifica che un valore sia stato scritto nel database"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if user:
            actual_value = getattr(user, field, None)
            print(f"[DB CHECK] {field}: atteso={value}, salvato={actual_value}")
            return actual_value == value
        return False
    finally:
        db.close()
