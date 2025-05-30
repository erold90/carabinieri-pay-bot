"""
Configuration settings for CarabinieriPayBot
"""
import os
from datetime import datetime
import pytz

# Environment
ENV = os.getenv('ENV', 'development')
DEBUG = ENV == 'development'

# Database
DATABASE_URL = os.getenv('DATABASE_URL')

# Timezone
TIMEZONE = pytz.timezone('Europe/Rome')

# Bot settings
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', os.getenv('BOT_TOKEN'))
MAX_OVERTIME_HOURS_MONTHLY = 55
ANNUAL_LEAVE_DAYS = 32

# Current date
def get_current_date():
    return datetime.now(TIMEZONE).date()

def get_current_datetime():
    return datetime.now(TIMEZONE)

# Conversation states
(
    SELECT_DATE,
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
) = range(12)