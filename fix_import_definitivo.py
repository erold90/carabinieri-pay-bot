#!/usr/bin/env python3
import subprocess
import sys

def run_command(cmd, shell=True):
    """Esegue comando e ritorna risultato"""
    print(f"🔄 Eseguo: {cmd}")
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Errore: {result.stderr}")
        return False
    if result.stdout:
        print(f"✅ {result.stdout.strip()}")
    return True

print("🔧 Fix definitivo import service_handler.py")
print("=" * 50)

# Contenuto corretto della sezione import
correct_imports = '''"""
Service registration handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from database.models import User, Service, ServiceType, TravelSheet
from config.settings import (
    SELECT_DATE, SELECT_TIME, SELECT_SERVICE_TYPE, SERVICE_DETAILS,
    TRAVEL_DETAILS, TRAVEL_TYPE, MEAL_DETAILS, CONFIRM_SERVICE
)
from config.constants import SUPER_HOLIDAYS
from utils.keyboards import (
    get_date_keyboard, get_time_keyboard, get_service_type_keyboard,
    get_yes_no_keyboard, get_mission_type_keyboard, get_meal_keyboard,
    get_confirm_keyboard
)
from utils.formatters import format_currency, format_date, format_time_range, format_hours
from services.calculation_service import (
    is_holiday, is_super_holiday, calculate_service_total
)
from handlers.start_handler import start_command

'''

print("1️⃣ Leggo il file attuale...")
with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# Trova dove inizia la prima funzione
first_function = content.find('async def new_service_command')

if first_function == -1:
    print("❌ Non trovo la funzione new_service_command")
    sys.exit(1)

# Ricostruisci il file con gli import corretti
new_content = correct_imports + content[first_function:]

print("2️⃣ Scrivo il file corretto...")
with open('handlers/service_handler.py', 'w') as f:
    f.write(new_content)

print("✅ File corretto!")

# Git operations
print("\n3️⃣ Git add...")
run_command("git add handlers/service_handler.py")

print("\n4️⃣ Git commit...")
run_command('git commit -m "fix: sistemato definitivamente import in service_handler"')

print("\n5️⃣ Git push...")
run_command("git push origin main")

print("\n" + "=" * 50)
print("✅ Fix completato e pushato!")
print("\n📊 Monitora il deploy con:")
print("railway logs --tail")
