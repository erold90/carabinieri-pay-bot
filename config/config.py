"""
Configurazione centralizzata per CarabinieriPayBot
"""
import os
from datetime import datetime
import pytz
import logging

# Environment
ENV = os.getenv('ENV', 'development')
DEBUG = ENV == 'development'

# Bot Token - prova tutte le varianti possibili
BOT_TOKEN = (
    os.getenv('TELEGRAM_BOT_TOKEN') or 
    os.getenv('BOT_TOKEN') or
    os.getenv('TG_BOT_TOKEN')
)

# Database
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Timezone
TIMEZONE = pytz.timezone('Europe/Rome')

# Logging
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

# Limiti
MAX_OVERTIME_HOURS_MONTHLY = 55
ANNUAL_LEAVE_DAYS = 32

# Clean chat
CLEAN_CHAT_ENABLED = True
KEEP_ONLY_LAST_MESSAGE = True

# Funzioni helper
def get_current_date():
    """Ottieni data corrente nel timezone corretto"""
    return datetime.now(TIMEZONE).date()

def get_current_datetime():
    """Ottieni datetime corrente nel timezone corretto"""
    return datetime.now(TIMEZONE)

# Validazione
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN non configurato!")

# Stati conversazione
(
    SELECT_DATE,
    SETUP_RANK,
    SETUP_COMMAND,
    SETUP_IRPEF,
    SETUP_LEAVE,
    SELECT_TIME,
    SELECT_SERVICE_TYPE,
    SERVICE_DETAILS,
    TRAVEL_DETAILS,
    TRAVEL_TYPE,
    MEAL_DETAILS,
    CONFIRM_SERVICE,
    PAYMENT_DETAILS,
    SELECT_TRAVEL_SHEETS,
    LEAVE_DATES,
    LEAVE_TYPE
) = range(16)
