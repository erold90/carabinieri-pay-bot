"""
Keyboard utilities for CarabinieriPayBot
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from config.constants import RANKS, SERVICE_TYPES

def get_date_keyboard(prefix="date"):
    """Get date selection keyboard"""
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    keyboard = [
        [
            InlineKeyboardButton(
                f"📍 Oggi {today.strftime('%d/%m')}", 
                callback_data=f"{prefix}_today"
            )
        ],
        [
            InlineKeyboardButton(
                f"📍 Ieri {yesterday.strftime('%d/%m')}", 
                callback_data=f"{prefix}_yesterday"
            )
        ],
        [
            InlineKeyboardButton(
                "📅 Altro giorno", 
                callback_data=f"{prefix}_other"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_time_keyboard(hour_range=range(0, 24), prefix="time"):
    """Get time selection keyboard"""
    keyboard = []
    
    # Hours in rows of 6
    for i in range(0, 24, 6):
        row = []
        for h in range(i, min(i + 6, 24)):
            if h in hour_range:
                row.append(InlineKeyboardButton(
                    f"{h:02d}:00",
                    callback_data=f"{prefix}_{h}"
                ))
        if row:
            keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

def get_service_type_keyboard():
    """Get service type selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("🚔 SCORTA (con viaggi)", callback_data="service_type_ESCORT")],
        [InlineKeyboardButton("📍 LOCALE (solo sede)", callback_data="service_type_LOCAL")],
        [InlineKeyboardButton("✈️ MISSIONE (generico)", callback_data="service_type_MISSION")]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_yes_no_keyboard(prefix):
    """Get yes/no keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Sì", callback_data=f"{prefix}_yes"),
            InlineKeyboardButton("❌ No", callback_data=f"{prefix}_no")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_mission_type_keyboard():
    """Get mission payment type keyboard"""
    keyboard = [
        [
            InlineKeyboardButton(
                "📋 ORDINARIO (Documentato)",
                callback_data="mission_type_ordinary"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 FORFETTARIO (€110 netti/24h)",
                callback_data="mission_type_forfeit"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_meal_keyboard():
    """Get meal selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("⭕ Nessuno", callback_data="meals_0")],
        [InlineKeyboardButton("1️⃣ Solo uno", callback_data="meals_1")],
        [InlineKeyboardButton("2️⃣ Entrambi", callback_data="meals_2")]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_rank_keyboard():
    """Get rank selection keyboard"""
    keyboard = []
    
    for i in range(0, len(RANKS), 2):
        row = []
        for j in range(i, min(i + 2, len(RANKS))):
            row.append(InlineKeyboardButton(
                RANKS[j],
                callback_data=f"rank_{j}"
            ))
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

def get_irpef_keyboard():
    """Get IRPEF rate keyboard with descriptions"""
    keyboard = [
        [
            InlineKeyboardButton("23% (fino a 15k€)", callback_data="irpef_23"),
            InlineKeyboardButton("25% (15-28k€)", callback_data="irpef_25")
        ],
        [
            InlineKeyboardButton("27% (media)", callback_data="irpef_27"),
            InlineKeyboardButton("35% (28-50k€)", callback_data="irpef_35")
        ],
        [
            InlineKeyboardButton("43% (oltre 50k€)", callback_data="irpef_43")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard(callback_data="back"):
    """Get back button keyboard"""
    keyboard = [
        [InlineKeyboardButton("⬅️ Indietro", callback_data=callback_data)]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_confirm_keyboard(prefix="confirm"):
    """Get confirm/cancel keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Conferma", callback_data=f"{prefix}_yes"),
            InlineKeyboardButton("❌ Annulla", callback_data=f"{prefix}_no")
        ],
        [InlineKeyboardButton("📝 Modifica", callback_data=f"{prefix}_edit")]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_month_keyboard(year):
    """Get month selection keyboard"""
    months = [
        "Gennaio", "Febbraio", "Marzo", "Aprile",
        "Maggio", "Giugno", "Luglio", "Agosto",
        "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    
    keyboard = []
    for i in range(0, 12, 3):
        row = []
        for j in range(i, min(i + 3, 12)):
            row.append(InlineKeyboardButton(
                months[j],
                callback_data=f"month_{year}_{j+1}"
            ))
        keyboard.append(row)
    
    return InlineKeyboardMarkup(keyboard)

def get_leave_type_keyboard():
    """Get leave type keyboard"""
    keyboard = [
        [InlineKeyboardButton("🏖️ Licenza ordinaria 2024", callback_data="leave_type_current")],
        [InlineKeyboardButton("📅 Licenza ordinaria 2023", callback_data="leave_type_previous")],
        [InlineKeyboardButton("🏥 Malattia", callback_data="leave_type_sick")],
        [InlineKeyboardButton("🩸 Donazione sangue", callback_data="leave_type_blood")],
        [InlineKeyboardButton("👨‍👩‍👧 L.104", callback_data="leave_type_104")],
        [InlineKeyboardButton("📚 Permesso studio", callback_data="leave_type_study")],
        [InlineKeyboardButton("🎊 Congedo matrimoniale", callback_data="leave_type_marriage")],
        [InlineKeyboardButton("⚖️ Altro permesso", callback_data="leave_type_other")]
    ]
    
    return InlineKeyboardMarkup(keyboard)