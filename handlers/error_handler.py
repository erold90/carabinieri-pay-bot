"""
Error handler migliorato con gestione specifica per tipo
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import NetworkError, TimedOut, RetryAfter, BadRequest
import logging
import traceback
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorHandler:
    """Gestisce gli errori in modo specifico per tipo"""
    
    def __init__(self):
        self.error_count = {}
        self.last_error_time = {}
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce errori con logica specifica per tipo"""
        error = context.error
        user_id = None
        
        if update and update.effective_user:
            user_id = update.effective_user.id
        
        # Log dell'errore
        logger.error(f"Errore: {type(error).__name__}: {error}", exc_info=True)
        
        # Gestione specifica per tipo di errore
        if isinstance(error, NetworkError):
            await self._handle_network_error(update, context)
        elif isinstance(error, TimedOut):
            await self._handle_timeout_error(update, context)
        elif isinstance(error, RetryAfter):
            await self._handle_rate_limit_error(update, context, error)
        elif isinstance(error, BadRequest):
            await self._handle_bad_request_error(update, context, error)
        else:
            await self._handle_generic_error(update, context)
        
        # Traccia errori per utente
        if user_id:
            self._track_error(user_id, error)
    
    async def _handle_network_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce errori di rete"""
        logger.warning("Errore di rete temporaneo")
        # Non notificare l'utente per errori di rete transitori
    
    async def _handle_timeout_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce timeout"""
        logger.warning("Timeout nella richiesta")
        # Non notificare l'utente per timeout
    
    async def _handle_rate_limit_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: RetryAfter):
        """Gestisce rate limiting"""
        logger.warning(f"Rate limit raggiunto. Riprova tra {error.retry_after} secondi")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    f"⏳ Troppe richieste. Riprova tra {error.retry_after} secondi."
                )
            except:
                pass
    
    async def _handle_bad_request_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE, error: BadRequest):
        """Gestisce richieste malformate"""
        logger.error(f"Bad request: {error}")
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Richiesta non valida. Riprova o usa /start"
                )
            except:
                pass
    
    async def _handle_generic_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce errori generici"""
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Si è verificato un errore. Riprova o usa /start per ricominciare."
                )
            except:
                pass
        
        # Invia report dettagliato agli admin (se configurato)
        if hasattr(context.bot_data, 'admin_chat_id'):
            error_report = self._create_error_report(update, context.error)
            try:
                await context.bot.send_message(
                    chat_id=context.bot_data['admin_chat_id'],
                    text=error_report,
                    parse_mode='HTML'
                )
            except:
                pass
    
    def _track_error(self, user_id: int, error: Exception):
        """Traccia errori per utente per identificare problemi ricorrenti"""
        error_type = type(error).__name__
        key = f"{user_id}:{error_type}"
        
        self.error_count[key] = self.error_count.get(key, 0) + 1
        self.last_error_time[key] = datetime.now()
        
        # Log se un utente ha troppi errori
        if self.error_count[key] > 10:
            logger.warning(f"Utente {user_id} ha generato {self.error_count[key]} errori di tipo {error_type}")
    
    def _create_error_report(self, update: Update, error: Exception) -> str:
        """Crea report dettagliato dell'errore"""
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        
        report = f"<b>🚨 ERROR REPORT</b>\n\n"
        report += f"<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += f"<b>Error:</b> {type(error).__name__}\n"
        report += f"<b>Message:</b> {str(error)}\n\n"
        
        if update:
            if update.effective_user:
                report += f"<b>User:</b> {update.effective_user.id} (@{update.effective_user.username})\n"
            if update.effective_chat:
                report += f"<b>Chat:</b> {update.effective_chat.id}\n"
            if update.effective_message:
                report += f"<b>Message:</b> {update.effective_message.text[:100]}\n"
        
        report += f"\n<b>Traceback:</b>\n<code>{tb[:3000]}</code>"
        
        return report
