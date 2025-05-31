"""
Gestore centralizzato per la registrazione degli handler
"""
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

class HandlerManager:
    """Gestisce la registrazione di tutti gli handler in modo organizzato"""
    
    def __init__(self, application: Application):
        self.app = application
    
    def register_all_handlers(self):
        """Registra tutti gli handler in modo organizzato"""
        self._register_command_handlers()
        self._register_callback_handlers()
        self._register_conversation_handlers()
        self._register_message_handlers()
        self._register_error_handler()
    
    def _register_command_handlers(self):
        """Registra tutti i command handler"""
        from handlers.start_handler import start_command
        from handlers.service_handler import new_service_command
        from handlers.overtime_handler import overtime_command
        from handlers.travel_sheet_handler import travel_sheets_command
        from handlers.leave_handler import leave_command
        from handlers.settings_handler import settings_command
        from handlers.report_handler import (
            today_command, yesterday_command, week_command,
            month_command, year_command, export_command
        )
        
        commands = {
            "start": start_command,
            "nuovo": new_service_command,
            "scorta": new_service_command,
            "straordinari": overtime_command,
            "fv": travel_sheets_command,
            "licenze": leave_command,
            "impostazioni": settings_command,
            "oggi": today_command,
            "ieri": yesterday_command,
            "settimana": week_command,
            "mese": month_command,
            "anno": year_command,
            "export": export_command
        }
        
        for command, handler in commands.items():
            self.app.add_handler(CommandHandler(command, handler))
    
    def _register_callback_handlers(self):
        """Registra callback handler con pattern"""
        from handlers.start_handler import dashboard_callback
        from handlers.overtime_handler import overtime_callback
        from handlers.leave_handler import leave_callback
        from handlers.travel_sheet_handler import travel_sheet_callback
        from handlers.settings_handler import settings_callback
        from handlers.rest_handler import rest_callback
        
        callbacks = {
            "^dashboard_": dashboard_callback,
            "^overtime_": overtime_callback,
            "^leave_": leave_callback,
            "^fv_": travel_sheet_callback,
            "^settings_": settings_callback,
            "^rest_": rest_callback
        }
        
        for pattern, handler in callbacks.items():
            self.app.add_handler(CallbackQueryHandler(handler, pattern=pattern))
    
    def _register_conversation_handlers(self):
        """Registra conversation handler"""
        from handlers.service_handler import service_conversation_handler
        from handlers.setup_handler import setup_conversation_handler
        
        self.app.add_handler(service_conversation_handler)
        self.app.add_handler(setup_conversation_handler)
    
    def _register_message_handlers(self):
        """Registra message handler"""
        from handlers.input_handler import InputHandler
        
        # Usa un gestore centralizzato per gli input
        input_handler = InputHandler()
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, input_handler.handle)
        )
    
    def _register_error_handler(self):
        """Registra error handler migliorato"""
        from handlers.error_handler import ErrorHandler
        
        error_handler = ErrorHandler()
        self.app.add_error_handler(error_handler.handle)
