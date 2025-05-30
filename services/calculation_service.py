"""
Service for all financial calculations
"""
from datetime import date, timedelta, time, datetime
from sqlalchemy.orm import Session
import holidays

from database.models import User, Service, Overtime, OvertimeType, ServiceType
from config.constants import OVERTIME_RATES, SERVICE_ALLOWANCES, MISSION_RATES, FORFEIT_RATES, MEAL_RATES, SUPER_HOLIDAYS

def calculate_easter(year):
    """Calcola la data di Pasqua per un dato anno usando l'algoritmo di Gauss"""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)

def is_holiday(d: date, patron_saint_date: date = None) -> bool:
    """Checks if a date is a holiday in Italy, including Sundays and local patron saint day."""
    it_holidays = holidays.country_holidays('IT', years=d.year)
    
    # Aggiungi Pasqua e Pasquetta manualmente se non presenti
    easter = calculate_easter(d.year)
    easter_monday = easter + timedelta(days=1)
    
    # Aggiungi le date se non già presenti
    if easter not in it_holidays:
        it_holidays[easter] = "Pasqua"
    if easter_monday not in it_holidays:
        it_holidays[easter_monday] = "Pasquetta"
    
    if patron_saint_date:
        it_holidays[patron_saint_date] = "Santo Patrono"
    
    return d in it_holidays or d.weekday() == 6  # 6 = domenica

def is_super_holiday(d: date) -> bool:
    """Checks if a date is a super holiday."""
    # Calcola Pasqua per l'anno corrente
    easter_date = calculate_easter(d.year)
    
    # Controlla se è Pasqua o Pasquetta
    if d == easter_date or d == easter_date + timedelta(days=1):
        return True
    
    # Controlla le altre super festività
    return (d.month, d.day) in SUPER_HOLIDAYS

def get_overtime_type(dt: datetime, is_h: bool) -> OvertimeType:
    """Determines the type of overtime based on time and holiday status."""
    if is_h:
        return OvertimeType.HOLIDAY_NIGHT if dt.hour >= 22 or dt.hour < 6 else OvertimeType.HOLIDAY_DAY
    else:
        return OvertimeType.WEEKDAY_NIGHT if dt.hour >= 22 or dt.hour < 6 else OvertimeType.WEEKDAY_DAY

def calculate_service_total(db: Session, user: User, service: Service) -> dict:
    """
    Calculates all net amounts for a single service event.
    This is the core calculation engine of the bot.
    """
    calculations = {
        'overtime': {},
        'allowances': {},
        'mission': {},
        'totals': {'overtime': 0, 'allowances': 0, 'mission': 0, 'total': 0}
    }

    # 1. Calculate Allowances
    # ========================
    allowances = {}
    if service.called_from_rest or service.called_from_leave:
        allowances['compensation'] = SERVICE_ALLOWANCES['compensation']
    
    if service.is_super_holiday:
        allowances['super_holiday_presence'] = SERVICE_ALLOWANCES['super_holiday_presence']
    elif service.is_holiday:
        allowances['holiday_presence'] = SERVICE_ALLOWANCES['holiday_presence']

    if service.total_hours >= 3:
        allowances['external_service'] = SERVICE_ALLOWANCES['external_service']
        if service.is_double_shift:
             allowances['external_service_2'] = SERVICE_ALLOWANCES['external_service']

    # Territory Control (simplified check)
    if time(18, 0) <= service.start_time.time() < time(22, 0) or time(18, 0) < service.end_time.time() < time(22, 0):
         if service.total_hours >= 3:
            allowances['territory_control_evening'] = SERVICE_ALLOWANCES['territory_control_evening']
    if service.start_time.time() >= time(22, 0) or service.end_time.time() <= time(3,0) or service.start_time.time() < time(3,0):
        if service.total_hours >= 3:
            allowances['territory_control_night'] = SERVICE_ALLOWANCES['territory_control_night']
    
    calculations['allowances'] = allowances
    calculations['totals']['allowances'] = sum(allowances.values())

    # 2. Calculate Overtime and Mission Pay
    # =====================================
    extra_hours = service.total_hours - user.base_shift_hours
    if extra_hours <= 0:
        extra_hours = 0
    
    overtime = {}
    mission = {}

    if service.service_type == ServiceType.ESCORT and service.travel_sheet_number:
        # --- SCORTA LOGIC ---
        # Passive travel (with VIP) is paid as OVERTIME
        passive_extra = min(extra_hours, service.passive_travel_hours)
        if passive_extra > 0:
            # Simplified: assuming all passive travel is of one type for now
            ot_type_passive = get_overtime_type(service.start_time, service.is_holiday or service.is_super_holiday)
            rate = OVERTIME_RATES[ot_type_passive.value.lower()]
            amount = passive_extra * rate
            overtime[ot_type_passive.value] = {'hours': passive_extra, 'rate': rate, 'amount': amount}
            extra_hours -= passive_extra

        # Active travel (alone) is paid as MISSION ALLOWANCE
        active_extra = min(extra_hours, service.active_travel_hours)
        if active_extra > 0:
            mission['active_travel_allowance'] = active_extra * MISSION_RATES['travel_hourly']
            extra_hours -= active_extra
    
    # Remaining extra hours are standard overtime
    if extra_hours > 0:
        ot_type_generic = get_overtime_type(service.start_time + timedelta(hours=user.base_shift_hours), service.is_holiday or service.is_super_holiday)
        rate = OVERTIME_RATES[ot_type_generic.value.lower()]
        amount = extra_hours * rate
        if ot_type_generic.value in overtime:
            overtime[ot_type_generic.value]['hours'] += extra_hours
            overtime[ot_type_generic.value]['amount'] += amount
        else:
            overtime[ot_type_generic.value] = {'hours': extra_hours, 'rate': rate, 'amount': amount}

    calculations['overtime'] = overtime
    calculations['totals']['overtime'] = sum(v['amount'] for v in overtime.values())

    # 3. Calculate Mission Reimbursements
    # ===================================
    if service.travel_sheet_number:
        if service.mission_type == 'FORFEIT':
            num_24h = service.total_hours // 24
            rem_hours = service.total_hours % 24
            forfeit_amount = num_24h * FORFEIT_RATES['24h']
            if rem_hours >= 12:
                forfeit_amount += FORFEIT_RATES['12h_extra']
            mission['forfeit'] = forfeit_amount
        else: # ORDINARY
            mission['daily_allowance'] = (service.total_hours / 24) * MISSION_RATES['daily_allowance']
            # Simplified meal calculation
            if service.meal_reimbursement > 0:
                 mission['meal_reimbursement'] = service.meal_reimbursement
    
    calculations['mission'] = mission
    calculations['totals']['mission'] = sum(mission.values())

    # Final Total
    calculations['totals']['total'] = calculations['totals']['overtime'] + calculations['totals']['allowances'] + calculations['totals']['mission']
    
    return calculations

def calculate_month_totals(db, user_id, month, year):
    """Calculate monthly totals with error handling"""
    try:
        # Get services for the month
        from sqlalchemy import extract
        from database.models import Service
        
        services = db.query(Service).filter(
            Service.user_id == user_id,
            extract('month', Service.date) == month,
            extract('year', Service.date) == year
        ).all()
        
        # Initialize totals
        result = {
            'days_worked': len(services),
            'total_hours': sum(s.total_hours for s in services) if services else 0,
            'paid_overtime': 0,
            'paid_hours': 0,
            'unpaid_overtime': 0,
            'unpaid_hours': 0,
            'allowances': sum(s.allowances_amount for s in services) if services else 0,
            'missions': sum(s.mission_amount for s in services) if services else 0,
            'total': sum(s.total_amount for s in services) if services else 0
        }
        
        # Get overtime data
        from database.models import Overtime
        overtimes = db.query(Overtime).filter(
            Overtime.user_id == user_id,
            extract('month', Overtime.date) == month,
            extract('year', Overtime.date) == year
        ).all()
        
        for ot in overtimes:
            if ot.is_paid:
                result['paid_overtime'] += ot.amount
                result['paid_hours'] += ot.hours
            else:
                result['unpaid_overtime'] += ot.amount
                result['unpaid_hours'] += ot.hours
        
        return result
        
    except Exception as e:
        print(f"Errore in calculate_month_totals: {e}")
        # Return default values
        return {
            'days_worked': 0,
            'total_hours': 0,
            'paid_overtime': 0,
            'paid_hours': 0,
            'unpaid_overtime': 0,
            'unpaid_hours': 0,
            'allowances': 0,
            'missions': 0,
            'total': 0
        }
