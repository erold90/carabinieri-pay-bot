"""
Service for all financial calculations - COMPLETE VERSION
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
    """Checks if a date is a holiday in Italy"""
    it_holidays = holidays.country_holidays('IT', years=d.year)
    
    # Aggiungi Pasqua e Pasquetta
    easter = calculate_easter(d.year)
    easter_monday = easter + timedelta(days=1)
    
    if easter not in it_holidays:
        it_holidays[easter] = "Pasqua"
    if easter_monday not in it_holidays:
        it_holidays[easter_monday] = "Pasquetta"
    
    if patron_saint_date and patron_saint_date.year == d.year and patron_saint_date.month == d.month and patron_saint_date.day == d.day:
        it_holidays[d] = "Santo Patrono"
    
    return d in it_holidays or d.weekday() == 6  # 6 = domenica

def is_super_holiday(d: date) -> bool:
    """Checks if a date is a super holiday"""
    easter_date = calculate_easter(d.year)
    
    if d == easter_date or d == easter_date + timedelta(days=1):
        return True
    
    return (d.month, d.day) in SUPER_HOLIDAYS

def calculate_overtime_by_hour(start_time: datetime, end_time: datetime, is_holiday: bool, 
                              base_hours: int = 6, recovery_hours: float = 0) -> dict:
    """Calcola straordinari ora per ora con le fasce orarie corrette"""
    overtime_details = {}
    current = start_time + timedelta(hours=base_hours)  # Skip ore ordinarie
    
    # Se ci sono ore di recupero, saltale
    if recovery_hours > 0:
        current += timedelta(hours=recovery_hours)
    
    # Calcola ora per ora
    while current < end_time:
        hour = current.hour
        
        # Determina tipo di straordinario
        if is_holiday:
            if 22 <= hour or hour < 6:
                ot_type = OvertimeType.HOLIDAY_NIGHT
            else:
                ot_type = OvertimeType.HOLIDAY_DAY
        else:
            if 22 <= hour or hour < 6:
                ot_type = OvertimeType.WEEKDAY_NIGHT
            else:
                ot_type = OvertimeType.WEEKDAY_DAY
        
        # Aggiungi al totale
        if ot_type.value not in overtime_details:
            overtime_details[ot_type.value] = {
                'hours': 0,
                'rate': OVERTIME_RATES[ot_type.value.lower()],
                'amount': 0
            }
        
        # Calcola frazione di ora
        next_hour = current + timedelta(hours=1)
        if next_hour > end_time:
            fraction = (end_time - current).total_seconds() / 3600
        else:
            fraction = 1.0
        
        overtime_details[ot_type.value]['hours'] += fraction
        overtime_details[ot_type.value]['amount'] += fraction * overtime_details[ot_type.value]['rate']
        
        current = next_hour
    
    return overtime_details

def calculate_territory_control(start_time: datetime, end_time: datetime, total_hours: float) -> dict:
    """Calcola indennità controllo territorio"""
    allowances = {}
    
    if total_hours < 3:
        return allowances
    
    # Controllo territorio serale (18:00-21:59)
    evening_start = start_time.replace(hour=18, minute=0, second=0)
    evening_end = start_time.replace(hour=22, minute=0, second=0)
    
    # Se il servizio attraversa la fascia serale
    if start_time < evening_end and end_time > evening_start:
        actual_start = max(start_time, evening_start)
        actual_end = min(end_time, evening_end)
        
        if actual_end > actual_start:
            hours_in_evening = (actual_end - actual_start).total_seconds() / 3600
            if hours_in_evening >= 3:
                allowances['territory_control_evening'] = SERVICE_ALLOWANCES['territory_control_evening']
    
    # Controllo territorio notturno (22:00-03:00)
    night_start = start_time.replace(hour=22, minute=0, second=0)
    night_end = (start_time + timedelta(days=1)).replace(hour=3, minute=0, second=0)
    
    # Se inizia nel giorno precedente
    if start_time.hour < 3:
        night_start = (start_time - timedelta(days=1)).replace(hour=22, minute=0, second=0)
        night_end = start_time.replace(hour=3, minute=0, second=0)
    
    # Se il servizio attraversa la fascia notturna
    if start_time < night_end and end_time > night_start:
        actual_start = max(start_time, night_start)
        actual_end = min(end_time, night_end)
        
        if actual_end > actual_start:
            hours_in_night = (actual_end - actual_start).total_seconds() / 3600
            if hours_in_night >= 3:
                allowances['territory_control_night'] = SERVICE_ALLOWANCES['territory_control_night']
    
    return allowances

def calculate_mission_allowances(service: Service, total_hours: float) -> dict:
    """Calcola compensi missione"""
    mission = {}
    
    if service.mission_type == 'FORFEIT':
        # Forfettario
        num_24h = int(total_hours // 24)
        rem_hours = total_hours % 24
        
        forfeit_amount = num_24h * FORFEIT_RATES['24h']
        if rem_hours >= 12:
            forfeit_amount += FORFEIT_RATES['12h_extra']
        
        mission['forfeit'] = forfeit_amount
    else:
        # Ordinario
        # Diaria
        if total_hours >= 24:
            mission['daily_allowance'] = MISSION_RATES['daily_allowance'] * (total_hours / 24)
        else:
            mission['hourly_allowance'] = MISSION_RATES['hourly_allowance'] * total_hours
        
        # Rimborso km
        if service.km_total > 0:
            mission['km_reimbursement'] = service.km_total * MISSION_RATES['km_rate']
        
        # Rimborso pasti
        meals_entitled = 0
        if total_hours >= 8:
            meals_entitled = 1
        if total_hours >= 12:
            meals_entitled = 2
        
        if hasattr(service, 'meals_not_consumed') and service.meals_not_consumed > 0:
            if service.meals_not_consumed == 1:
                mission['meal_reimbursement'] = MEAL_RATES['single_meal_net']
            elif service.meals_not_consumed == 2:
                mission['meal_reimbursement'] = MEAL_RATES['double_meal_net']
    
    return mission

def calculate_service_total(db: Session, user: User, service: Service) -> dict:
    """
    Calculates ALL net amounts for a service - COMPLETE VERSION
    """
    calculations = {
        'overtime': {},
        'allowances': {},
        'mission': {},
        'totals': {'overtime': 0, 'allowances': 0, 'mission': 0, 'total': 0}
    }
    
    # 1. INDENNITÀ GIORNALIERE
    allowances = {}
    
    # Compensazione per richiamo
    if service.called_from_rest or service.called_from_leave:
        allowances['compensation'] = SERVICE_ALLOWANCES['compensation']
    
    # Presenza festiva
    if service.is_super_holiday:
        allowances['super_holiday_presence'] = SERVICE_ALLOWANCES['super_holiday_presence']
    elif service.is_holiday:
        allowances['holiday_presence'] = SERVICE_ALLOWANCES['holiday_presence']
    
    # Servizio esterno (min 3h)
    if service.total_hours >= 3:
        allowances['external_service'] = SERVICE_ALLOWANCES['external_service']
        if service.is_double_shift:
            allowances['external_service_2'] = SERVICE_ALLOWANCES['external_service']
    
    # Controllo territorio
    territory = calculate_territory_control(service.start_time, service.end_time, service.total_hours)
    allowances.update(territory)
    
    calculations['allowances'] = allowances
    calculations['totals']['allowances'] = sum(allowances.values())
    
    # 2. STRAORDINARI
    extra_hours = max(0, service.total_hours - user.base_shift_hours - service.recovery_hours)
    
    if service.service_type == ServiceType.ESCORT:
        # Per scorta: ore passive sono straordinario
        passive_overtime = min(extra_hours, service.passive_travel_hours)
        if passive_overtime > 0:
            ot_details = calculate_overtime_by_hour(
                service.start_time + timedelta(hours=user.base_shift_hours),
                service.start_time + timedelta(hours=user.base_shift_hours + passive_overtime),
                service.is_holiday or service.is_super_holiday,
                0  # già saltato il turno base
            )
            calculations['overtime'].update(ot_details)
            extra_hours -= passive_overtime
        
        # Ore attive come maggiorazione viaggio
        if service.active_travel_hours > 0:
            calculations['mission']['active_travel'] = service.active_travel_hours * MISSION_RATES['travel_hourly']
    
    # Straordinari rimanenti
    if extra_hours > 0:
        ot_details = calculate_overtime_by_hour(
            service.start_time,
            service.end_time,
            service.is_holiday or service.is_super_holiday,
            user.base_shift_hours,
            service.recovery_hours
        )
        
        # Merge con eventuali straordinari già calcolati
        for ot_type, details in ot_details.items():
            if ot_type in calculations['overtime']:
                calculations['overtime'][ot_type]['hours'] += details['hours']
                calculations['overtime'][ot_type]['amount'] += details['amount']
            else:
                calculations['overtime'][ot_type] = details
    
    calculations['totals']['overtime'] = sum(v['amount'] for v in calculations['overtime'].values())
    
    # 3. MISSIONI E RIMBORSI
    if service.service_type in [ServiceType.ESCORT, ServiceType.MISSION]:
        mission_allowances = calculate_mission_allowances(service, service.total_hours)
        calculations['mission'].update(mission_allowances)
    
    calculations['totals']['mission'] = sum(calculations['mission'].values())
    
    # 4. TOTALE FINALE
    calculations['totals']['total'] = (
        calculations['totals']['overtime'] + 
        calculations['totals']['allowances'] + 
        calculations['totals']['mission']
    )
    
    # 5. Salva nel servizio
    service.overtime_amount = calculations['totals']['overtime']
    service.allowances_amount = calculations['totals']['allowances']
    service.mission_amount = calculations['totals']['mission']
    service.total_amount = calculations['totals']['total']
    service.calculation_details = calculations
    
    # 6. Crea record straordinari nel DB
    if calculations['overtime']:
        for ot_type, details in calculations['overtime'].items():
            overtime = Overtime(
                user_id=user.id,
                service_id=service.id,
                date=service.date,
                hours=details['hours'],
                overtime_type=OvertimeType[ot_type],
                hourly_rate=details['rate'],
                amount=details['amount'],
                is_paid=False  # Default non pagato
            )
            db.add(overtime)
    
    return calculations

def calculate_month_totals(db, user_id, month, year):
    """Calculate complete monthly totals"""
    try:
        from sqlalchemy import extract
        from database.models import Service, Overtime
        
        # Servizi del mese
        services = db.query(Service).filter(
            Service.user_id == user_id,
            extract('month', Service.date) == month,
            extract('year', Service.date) == year
        ).all()
        
        # Straordinari del mese
        overtimes = db.query(Overtime).filter(
            Overtime.user_id == user_id,
            extract('month', Overtime.date) == month,
            extract('year', Overtime.date) == year
        ).all()
        
        result = {
            'days_worked': len(services),
            'total_hours': sum(s.total_hours for s in services) if services else 0,
            'paid_overtime': 0,
            'paid_hours': 0,
            'unpaid_overtime': 0,
            'unpaid_hours': 0,
            'allowances': sum(s.allowances_amount for s in services) if services else 0,
            'missions': sum(s.mission_amount for s in services) if services else 0,
            'total': sum(s.total_amount for s in services) if services else 0,
            # Dettagli aggiuntivi
            'double_shifts': sum(1 for s in services if s.is_double_shift),
            'holidays': sum(1 for s in services if s.is_holiday),
            'super_holidays': sum(1 for s in services if s.is_super_holiday),
            'escorts': sum(1 for s in services if s.service_type == ServiceType.ESCORT),
            'missions': sum(1 for s in services if s.service_type == ServiceType.MISSION),
            'total_km': sum(s.km_total for s in services if s.km_total),
            'recoveries': sum(s.recovery_hours for s in services if s.recovery_hours > 0)
        }
        
        # Separa straordinari pagati/non pagati
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
        return {
            'days_worked': 0,
            'total_hours': 0,
            'paid_overtime': 0,
            'paid_hours': 0,
            'unpaid_overtime': 0,
            'unpaid_hours': 0,
            'allowances': 0,
            'missions': 0,
            'total': 0,
            'double_shifts': 0,
            'holidays': 0,
            'super_holidays': 0,
            'escorts': 0,
            'missions': 0,
            'total_km': 0,
            'recoveries': 0
        }
