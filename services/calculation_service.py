"""
Service for all financial calculations
"""
from datetime import timedelta, date
from sqlalchemy import extract
import holidays

from database.models import Service, User
from config.constants import OVERTIME_RATES, SERVICE_ALLOWANCES, MISSION_RATES, FORFEIT_RATES, MEAL_RATES, SUPER_HOLIDAYS

def is_holiday(d: date) -> bool:
    """Checks if a date is a holiday in Italy."""
    it_holidays = holidays.country_holidays('IT')
    return d in it_holidays or d.weekday() == 6

def is_super_holiday(d: date) -> bool:
    """Checks if a date is a super holiday."""
    easter_date = holidays.easter(d.year)
    easter_monday = easter_date + timedelta(days=1)
    if d == easter_date or d == easter_monday:
        return True
    return (d.month, d.day) in SUPER_HOLIDAYS

def calculate_service_total(db, user, service):
    """
    Placeholder for single service calculation logic.
    """
    service.overtime_amount = 0
    service.allowances_amount = 0
    service.mission_amount = 0
    service.total_amount = 0
    return {
        'overtime': {}, 'allowances': {}, 'mission': {},
        'totals': {
            'overtime': 0, 'allowances': 0, 'mission': 0, 'total': 0
        }
    }

def calculate_month_totals(db, user_id, month, year):
    """Calculates all totals for a given user and month."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {'days_worked': 0, 'total_hours': 0, 'paid_overtime': 0, 'paid_hours': 0, 'unpaid_overtime': 0, 'unpaid_hours': 0, 'allowances': 0, 'missions': 0, 'total': 0}

    services = db.query(Service).filter(
        Service.user_id == user_id,
        extract('month', Service.date) == month,
        extract('year', Service.date) == year
    ).all()

    if not services:
        return {'days_worked': 0, 'total_hours': 0, 'paid_overtime': 0, 'paid_hours': 0, 'unpaid_overtime': 0, 'unpaid_hours': 0, 'allowances': 0, 'missions': 0, 'total': 0}

    days_worked = len(set(s.date for s in services))
    total_hours = sum(s.total_hours for s in services)
    allowances = sum(s.allowances_amount for s in services)
    missions = sum(s.mission_amount for s in services)
    paid_overtime = sum(s.overtime_amount for s in services)
    total_amount = paid_overtime + allowances + missions
    
    base_hours_total = days_worked * user.base_shift_hours
    overtime_hours = total_hours - base_hours_total if total_hours > base_hours_total else 0

    return {
        'days_worked': days_worked,
        'total_hours': total_hours,
        'paid_overtime': paid_overtime,
        'paid_hours': overtime_hours,
        'unpaid_overtime': 0,
        'unpaid_hours': 0,
        'allowances': allowances,
        'missions': missions,
        'total': total_amount
    }
