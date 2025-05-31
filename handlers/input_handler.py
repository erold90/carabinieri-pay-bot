"""
Gestore centralizzato per tutti gli input testuali
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging

from utils.validators import (
    validate_time_input, validate_date_input, 
    validate_number_input, sanitize_text_input
)

logger = logging.getLogger(__name__)

class InputHandler:
    """Gestisce tutti gli input testuali in modo centralizzato"""
    
    def __init__(self):
        self.handlers = {
            # Settings inputs
            'waiting_for_command': self._handle_command_input,
            'waiting_for_base_hours': self._handle_base_hours_input,
            'waiting_for_leave_value': self._handle_leave_value_input,
            
            # Route inputs
            'adding_route': self._handle_route_name_input,
            'adding_route_km': self._handle_route_km_input,
            
            # Date/time inputs
            'waiting_for_start_time': self._handle_start_time_input,
            'waiting_for_end_time': self._handle_end_time_input,
            'setting_patron_saint': self._handle_patron_saint_input,
            'setting_reminder_time': self._handle_reminder_time_input,
            
            # Payment inputs
            'waiting_for_paid_hours': self._handle_paid_hours_input,
            'waiting_for_fv_selection': self._handle_fv_selection_input,
            'waiting_for_fv_search': self._handle_fv_search_input
        }
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce l'input basandosi sullo stato corrente"""
        user_data = context.user_data
        
        # Trova il primo handler applicabile
        for state_key, handler_func in self.handlers.items():
            if user_data.get(state_key):
                try:
                    await handler_func(update, context)
                    return
                except Exception as e:
                    logger.error(f"Errore in {state_key}: {e}")
                    await update.message.reply_text(
                        "❌ Errore nell'elaborazione. Riprova."
                    )
                    # Reset dello stato
                    user_data[state_key] = False
                    return
        
        # Nessuno stato attivo - ignora o invia messaggio di aiuto
        await update.message.reply_text(
            "🤔 Non ho capito. Usa /start per vedere i comandi disponibili."
        )
    
    async def _handle_command_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce input del comando"""
        from handlers.settings_handler import handle_text_input
        await handle_text_input(update, context)
    
    async def _handle_base_hours_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce input ore base"""
        text = update.message.text.strip()
        hours = validate_number_input(text, min_val=1, max_val=24)
        
        if hours is None:
            await update.message.reply_text("❌ Inserisci un numero tra 1 e 24")
            return
        
        # Salva nel database
        from database.connection import SessionLocal
        from database.models import User
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(
                User.telegram_id == str(update.effective_user.id)
            ).first()
            
            user.base_shift_hours = int(hours)
            db.commit()
            
            await update.message.reply_text(
                f"✅ Turno base aggiornato: {int(hours)} ore"
            )
            
            context.user_data['waiting_for_base_hours'] = False
            
        finally:
            db.close()
    
    async def _handle_start_time_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce input orario inizio"""
        text = update.message.text.strip()
        hour, minute = validate_time_input(text)
        
        if hour is None:
            await update.message.reply_text(
                "❌ Formato non valido! Usa HH:MM (es: 08:30)"
            )
            return
        
        # Continua con la logica del servizio
        from handlers.service_handler import handle_time_input
        await handle_time_input(update, context)
    
    async def _handle_leave_value_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce input valore licenze"""
        from handlers.leave_handler import handle_leave_value_input
        await handle_leave_value_input(update, context)
    
    async def _handle_route_name_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce input nome percorso"""
        from handlers.leave_handler import handle_route_name_input
        await handle_route_name_input(update, context)
    
    async def _handle_route_km_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce input km percorso"""
        from handlers.leave_handler import handle_route_km_input
        await handle_route_km_input(update, context)
    
    async def _handle_patron_saint_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce input santo patrono"""
        from handlers.leave_handler import handle_patron_saint_input
        await handle_patron_saint_input(update, context)
    
    async def _handle_reminder_time_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce input orario reminder"""
        from handlers.leave_handler import handle_reminder_time_input
        await handle_reminder_time_input(update, context)
    
    async def _handle_paid_hours_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce input ore pagate"""
        from handlers.overtime_handler import handle_paid_hours_input
        await handle_paid_hours_input(update, context)
    
    async def _handle_fv_selection_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce selezione fogli viaggio"""
        from handlers.travel_sheet_handler import handle_travel_sheet_selection
        await handle_travel_sheet_selection(update, context)
    
    async def _handle_fv_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce ricerca fogli viaggio"""
        from handlers.travel_sheet_handler import handle_travel_sheet_search
        await handle_travel_sheet_search(update, context)
    
    async def _handle_end_time_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce input orario fine"""
        from handlers.service_handler import handle_time_input
        await handle_time_input(update, context)
