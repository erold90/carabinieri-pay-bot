"""
Validatori robusti per input utente
"""
import re
from datetime import datetime, date
from typing import Optional, Tuple

def validate_time_input(time_str: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Valida input orario in vari formati
    Ritorna (hour, minute) o (None, None)
    """
    patterns = [
        (r'^(\d{1,2}):(\d{2})$', lambda m: (int(m.group(1)), int(m.group(2)))),
        (r'^(\d{1,2})\.(\d{2})$', lambda m: (int(m.group(1)), int(m.group(2)))),
        (r'^(\d{2})(\d{2})$', lambda m: (int(m.group(1)), int(m.group(2)))),
        (r'^(\d{1,2})$', lambda m: (int(m.group(1)), 0))
    ]
    
    for pattern, parser in patterns:
        match = re.match(pattern, time_str.strip())
        if match:
            try:
                hour, minute = parser(match)
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return hour, minute
            except:
                pass
    
    return None, None

def validate_date_input(date_str: str) -> Optional[date]:
    """
    Valida input data nel formato GG/MM/AAAA
    """
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

def validate_number_input(text: str, min_val=None, max_val=None, allow_float=True) -> Optional[float]:
    """
    Valida input numerico con limiti opzionali
    """
    try:
        # Sostituisci virgola con punto
        text = text.strip().replace(',', '.')
        
        if allow_float:
            value = float(text)
        else:
            value = float(text)
            if value != int(value):
                return None
            value = int(value)
        
        if min_val is not None and value < min_val:
            return None
        if max_val is not None and value > max_val:
            return None
            
        return value
    except:
        return None

def sanitize_text_input(text: str, max_length=100, allow_emoji=False) -> str:
    """
    Sanitizza input testuale
    """
    if not text:
        return ""
    
    # Rimuovi caratteri di controllo
    text = ''.join(char for char in text if ord(char) >= 32 or char == '
')
    
    # Rimuovi emoji se non permesse
    if not allow_emoji:
        text = re.sub(r'[^\w\s\-.,!?€/@#()'"]', '', text, flags=re.UNICODE)
    
    # Trim e limita lunghezza
    text = text.strip()[:max_length]
    
    return text

def validate_selection_input(text: str, valid_options: list) -> Optional[list]:
    """
    Valida input di selezione multipla (es: "1,3,5" o "tutti")
    """
    text = text.strip().lower()
    
    if text == 'tutti':
        return valid_options
    
    try:
        # Parse numeri separati da virgola
        selections = []
        for part in text.split(','):
            num = int(part.strip())
            if num in valid_options:
                selections.append(num)
        
        return selections if selections else None
    except:
        return None
