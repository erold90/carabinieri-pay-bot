# utils/validators.py
"""Validatori per input utente"""
import re
from datetime import datetime, date

def validate_time_input(time_str: str) -> tuple:
    """Valida input orario"""
    patterns = [
        r'^(\d{1,2}):(\d{2})$',     # HH:MM
        r'^(\d{1,2})\.(\d{2})$',     # HH.MM
        r'^(\d{2})(\d{2})$',         # HHMM
        r'^(\d{1,2})$'               # H o HH
    ]
    
    for pattern in patterns:
        match = re.match(pattern, time_str.strip())
        if match:
            groups = match.groups()
            if len(groups) == 2:
                hour, minute = int(groups[0]), int(groups[1])
            else:
                hour, minute = int(groups[0]), 0
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return hour, minute
    
    return None, None

def validate_date_input(date_str: str) -> date:
    """Valida input data"""
    try:
        parts = date_str.strip().split('/')
        if len(parts) == 3:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            # Gestisci anno a 2 cifre
            if year < 100:
                year += 2000
            return date(year, month, day)
    except:
        pass
    return None

def validate_number_input(text: str, min_val=None, max_val=None) -> float:
    """Valida input numerico"""
    try:
        value = float(text.strip().replace(',', '.'))
        if min_val is not None and value < min_val:
            return None
        if max_val is not None and value > max_val:
            return None
        return value
    except:
        return None

def sanitize_text_input(text: str, max_length=100) -> str:
    """Sanitizza input testuale"""
    if not text:
        return ""
    
    # Rimuovi caratteri di controllo
    text = ''.join(char for char in text if ord(char) >= 32)
    
    # Trim e limita lunghezza
    text = text.strip()[:max_length]
    
    return text
