"""
Configurazione logging per CarabinieriPayBot
"""
import logging
import os

def setup_logging():
    """Configura il logging con livelli appropriati"""
    
    # Livello base: INFO in produzione, DEBUG in development
    level = logging.DEBUG if os.getenv('ENV') == 'development' else logging.INFO
    
    # Formato semplificato
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%H:%M:%S'  # Solo ora, senza data
    
    # Configurazione base
    logging.basicConfig(
        format=log_format,
        datefmt=date_format,
        level=level,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('bot.log', encoding='utf-8')
        ]
    )
    
    # Silenzia moduli verbosi
    noisy_modules = [
        'httpx',
        'httpcore', 
        'telegram.ext.ExtBot',
        'telegram.ext._application',
        'telegram.ext._updater',
        'telegram.ext._basehandler',
        'telegram._bot',
        'telegram._request',
        'urllib3.connectionpool',
        'asyncio'
    ]
    
    for module in noisy_modules:
        logging.getLogger(module).setLevel(logging.WARNING)
    
    # Log solo errori per alcuni moduli
    error_only_modules = [
        'telegram.error',
        'telegram.ext._utils.webhookhandler'
    ]
    
    for module in error_only_modules:
        logging.getLogger(module).setLevel(logging.ERROR)
    
    # Il nostro logger principale resta a INFO
    app_logger = logging.getLogger('__main__')
    app_logger.setLevel(logging.INFO)
    
    return app_logger

# Funzione helper per log colorati (opzionale)
def log_info(message):
    """Log con emoji per maggiore chiarezza"""
    logger = logging.getLogger('__main__')
    logger.info(f"ℹ️  {message}")

def log_success(message):
    """Log successo"""
    logger = logging.getLogger('__main__')
    logger.info(f"✅ {message}")

def log_error(message):
    """Log errore"""
    logger = logging.getLogger('__main__')
    logger.error(f"❌ {message}")

def log_warning(message):
    """Log warning"""
    logger = logging.getLogger('__main__')
    logger.warning(f"⚠️  {message}")
