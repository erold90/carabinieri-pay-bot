"""
Formatting utilities for CarabinieriPayBot
"""
from datetime import datetime, date
import locale

# Set Italian locale for date formatting
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'it_IT')
    except:
        pass  # Fallback to default

def format_currency(amount):
    """Format amount as currency"""
    if amount is None:
        return "€ 0,00"
    return f"€ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_date(date_obj):
    """Format date in Italian format"""
    if isinstance(date_obj, str):
        return date_obj
    
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    return date_obj.strftime("%d/%m/%Y")

def format_datetime(datetime_obj):
    """Format datetime in Italian format"""
    if isinstance(datetime_obj, str):
        return datetime_obj
    
    return datetime_obj.strftime("%d/%m/%Y %H:%M")

def format_month_year(date_obj):
    """Format month and year"""
    if isinstance(date_obj, str):
        return date_obj
    
    try:
        return date_obj.strftime("%B %Y").title()
    except:
        # Fallback if locale not set
        months = {
            1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
            5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
            9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
        }
        return f"{months[date_obj.month]} {date_obj.year}"

def format_hours(hours):
    """Format hours with proper singular/plural"""
    if hours == 1:
        return "1 ora"
    return f"{hours:.1f} ore".replace(".0", "")

def format_days(days):
    """Format days with proper singular/plural"""
    if days == 1:
        return "1 giorno"
    return f"{days} giorni"

def format_percentage(value, total):
    """Format percentage"""
    if total == 0:
        return "0%"
    percentage = (value / total) * 100
    return f"{percentage:.1f}%"

def format_time_range(start_time, end_time):
    """Format time range"""
    if isinstance(start_time, datetime):
        start = start_time.strftime("%H:%M")
    else:
        start = start_time
    
    if isinstance(end_time, datetime):
        end = end_time.strftime("%H:%M")
    else:
        end = end_time
    
    return f"{start}-{end}"

def format_service_summary(service):
    """Format service summary for display"""
    summary = f"📅 {format_date(service.date)}\n"
    summary += f"⏰ {format_time_range(service.start_time, service.end_time)} "
    summary += f"({format_hours(service.total_hours)})\n"
    
    if service.service_type == "ESCORT":
        summary += f"🚔 Scorta {service.destination}\n"
        if service.travel_sheet_number:
            summary += f"📋 F.V. {service.travel_sheet_number}\n"
    elif service.service_type == "LOCAL":
        summary += "📍 Servizio Locale\n"
    else:
        summary += "✈️ Missione\n"
    
    if service.is_super_holiday:
        summary += "🎄 SUPER-FESTIVO\n"
    elif service.is_holiday:
        summary += "🔴 Festivo\n"
    
    if service.is_double_shift:
        summary += "⚠️ Doppio turno\n"
    
    if service.called_from_leave:
        summary += "🏖️ Richiamato da licenza\n"
    elif service.called_from_rest:
        summary += "💤 Richiamato da riposo\n"
    
    summary += f"\n💰 Totale: {format_currency(service.total_amount)}"
    
    return summary

def format_travel_sheet_summary(travel_sheet):
    """Format travel sheet summary"""
    status = "✅ PAGATO" if travel_sheet.is_paid else "⏳ In attesa"
    summary = f"📋 F.V. {travel_sheet.sheet_number}\n"
    summary += f"📅 {format_date(travel_sheet.date)}\n"
    summary += f"📍 {travel_sheet.destination}\n"
    summary += f"💰 {format_currency(travel_sheet.amount)}\n"
    summary += f"📌 Stato: {status}"
    
    if travel_sheet.is_paid and travel_sheet.paid_date:
        summary += f"\n💳 Pagato il {format_date(travel_sheet.paid_date)}"
    
    return summary

def format_overtime_summary(overtime_hours, overtime_amount):
    """Format overtime summary"""
    if not overtime_hours:
        return "Nessuno straordinario"
    
    summary = f"⏰ {format_hours(overtime_hours)}\n"
    summary += f"💰 {format_currency(overtime_amount)}"
    
    return summary

def escape_markdown(text):
    """Escape special characters for Telegram MarkdownV2"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text