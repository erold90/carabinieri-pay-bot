"""
Calculation service for CarabinieriPayBot
"""
from datetime import datetime, time, date
from sqlalchemy.orm import Session

from database.models import User, Service, Overtime, OvertimeType
from config.constants import (
    OVERTIME_RATES, SERVICE_ALLOWANCES, MISSION_RATES, 
    MEAL_RATES, FORFEIT_RATES, SUPER_HOLIDAYS
)
from config.settings import get_current_date

def is_super_holiday(check_date):
    """Check if date is a super holiday"""
    # Fixed super holidays
    for month, day in SUPER_HOLIDAYS:
        if check_date.month == month and check_date.day == day:
            return True
    
    # TODO: Calculate Easter and Easter Monday dynamically
    # For now, these should be set in user settings
    
    return False

def is_holiday(check_date):
    """Check if date is a holiday (Sunday or festivity)"""
    # Sunday
    if check_date.weekday() == 6:
        return True
    
    # Check if super holiday (which are also holidays)
    if is_super_holiday(check_date):
        return True
    
    # TODO: Check patron saint and other holidays from user settings
    
    return False

def get_overtime_type(hour, is_holiday_day):
    """Get overtime type based on hour and day type"""
    if is_holiday_day:
        if 6 <= hour < 22:
            return OvertimeType.HOLIDAY_DAY
        else:
            return OvertimeType.HOLIDAY_NIGHT
    else:
        if 6 <= hour < 22:
            return OvertimeType.WEEKDAY_DAY
        else:
            return OvertimeType.WEEKDAY_NIGHT

def calculate_overtime_hours(start_time, end_time, base_hours, is_holiday_day):
    """Calculate overtime hours by type"""
    total_hours = (end_time - start_time).total_seconds() / 3600
    overtime_hours = max(0, total_hours - base_hours)
    
    if overtime_hours == 0:
        return {}
    
    # Calculate hours by type
    hours_by_type = {
        OvertimeType.WEEKDAY_DAY: 0,
        OvertimeType.WEEKDAY_NIGHT: 0,
        OvertimeType.HOLIDAY_DAY: 0,
        OvertimeType.HOLIDAY_NIGHT: 0
    }
    
    current = start_time
    overtime_start = start_time + timedelta(hours=base_hours)
    
    while current < end_time and current < overtime_start:
        current += timedelta(hours=1)
    
    while current < end_time:
        hour = current.hour
        overtime_type = get_overtime_type(hour, is_holiday_day)
        
        # Calculate minutes in this hour
        next_hour = current.replace(minute=0, second=0) + timedelta(hours=1)
        if next_hour > end_time:
            minutes = (end_time - current).total_seconds() / 60
        else:
            minutes = (next_hour - current).total_seconds() / 60
        
        hours_by_type[overtime_type] += minutes / 60
        current = next_hour
    
    # Remove zero entries
    return {k: v for k, v in hours_by_type.items() if v > 0}

def calculate_service_allowances(service: Service, user: User):
    """Calculate service allowances"""
    allowances = {}
    total = 0
    
    # External service (first shift)
    if service.total_hours >= 3:
        allowances['external_service'] = SERVICE_ALLOWANCES['external_service']
        total += SERVICE_ALLOWANCES['external_service']
    
    # Double shift (second external service)
    if service.is_double_shift:
        allowances['external_service_2'] = SERVICE_ALLOWANCES['external_service']
        total += SERVICE_ALLOWANCES['external_service']
    
    # Holiday presence
    if service.is_super_holiday:
        allowances['super_holiday_presence'] = SERVICE_ALLOWANCES['super_holiday_presence']
        total += SERVICE_ALLOWANCES['super_holiday_presence']
    elif service.is_holiday:
        allowances['holiday_presence'] = SERVICE_ALLOWANCES['holiday_presence']
        total += SERVICE_ALLOWANCES['holiday_presence']
    
    # Compensation (called from leave/rest)
    if service.called_from_leave or service.called_from_rest:
        allowances['compensation'] = SERVICE_ALLOWANCES['compensation']
        total += SERVICE_ALLOWANCES['compensation']
    
    # Territory control
    if service.service_type == "LOCAL":
        evening_hours = 0
        night_hours = 0
        
        current = service.start_time
        while current < service.end_time:
            hour = current.hour
            if 18 <= hour < 22:
                evening_hours += 1
            elif hour >= 22 or hour < 3:
                night_hours += 1
            current += timedelta(hours=1)
        
        if evening_hours >= 3:
            allowances['territory_control_evening'] = SERVICE_ALLOWANCES['territory_control_evening']
            total += SERVICE_ALLOWANCES['territory_control_evening']
        
        if night_hours >= 3:
            allowances['territory_control_night'] = SERVICE_ALLOWANCES['territory_control_night']
            total += SERVICE_ALLOWANCES['territory_control_night']
    
    return allowances, total

def calculate_escort_compensation(service: Service):
    """Calculate escort specific compensation"""
    compensation = {}
    total = 0
    
    # Active travel hours (without VIP)
    if service.active_travel_hours > 0:
        # Only hours exceeding base shift are paid
        base_hours = 6  # TODO: Get from user settings
        paid_hours = max(0, service.active_travel_hours - base_hours)
        if paid_hours > 0:
            compensation['active_travel'] = paid_hours * MISSION_RATES['travel_hourly']
            total += compensation['active_travel']
    
    # Passive travel hours (with VIP) - paid as overtime
    # This is handled in overtime calculation
    
    # Kilometers
    if service.km_total > 0:
        compensation['km'] = service.km_total * MISSION_RATES['km_rate']
        total += compensation['km']
    
    return compensation, total

def calculate_mission_compensation(service: Service):
    """Calculate mission compensation"""
    compensation = {}
    total = 0
    
    if service.mission_type == "FORFEIT":
        # Forfeit calculation
        if service.total_hours <= 24:
            compensation['forfeit_24h'] = FORFEIT_RATES['24h']
            total += FORFEIT_RATES['24h']
        else:
            compensation['forfeit_24h'] = FORFEIT_RATES['24h']
            total += FORFEIT_RATES['24h']
            
            # Additional 12h blocks
            additional_hours = service.total_hours - 24
            additional_blocks = int(additional_hours / 12) + (1 if additional_hours % 12 > 0 else 0)
            compensation['forfeit_extra'] = additional_blocks * FORFEIT_RATES['12h_extra']
            total += compensation['forfeit_extra']
    else:
        # Ordinary calculation
        # Daily allowance
        if service.total_hours >= 24:
            compensation['daily_allowance'] = MISSION_RATES['daily_allowance']
            total += MISSION_RATES['daily_allowance']
        else:
            # Hourly allowance
            compensation['hourly_allowance'] = service.total_hours * MISSION_RATES['hourly_allowance']
            total += compensation['hourly_allowance']
        
        # Meal reimbursement
        if service.meals_consumed < 2:
            meals_not_consumed = 2 - service.meals_consumed
            if meals_not_consumed == 1:
                compensation['meal_reimbursement'] = MEAL_RATES['single_meal_net']
                total += MEAL_RATES['single_meal_net']
            elif meals_not_consumed == 2:
                compensation['meal_reimbursement'] = MEAL_RATES['double_meal_net']
                total += MEAL_RATES['double_meal_net']
            
            # Reduce daily allowance to 40% if meals not consumed
            if 'daily_allowance' in compensation:
                compensation['daily_allowance'] *= 0.4
                total = sum(compensation.values())
    
    return compensation, total

def calculate_service_total(db: Session, user: User, service: Service):
    """Calculate total compensation for a service"""
    calculations = {
        'overtime': {},
        'allowances': {},
        'mission': {},
        'totals': {}
    }
    
    # 1. Calculate overtime
    overtime_total = 0
    if service.total_hours > user.base_shift_hours:
        overtime_by_type = calculate_overtime_hours(
            service.start_time, 
            service.end_time, 
            user.base_shift_hours,
            service.is_holiday
        )
        
        for ot_type, hours in overtime_by_type.items():
            rate = OVERTIME_RATES[ot_type.value.lower()]
            amount = hours * rate
            
            calculations['overtime'][ot_type.value] = {
                'hours': hours,
                'rate': rate,
                'amount': amount
            }
            overtime_total += amount
            
            # Save overtime record
            overtime = Overtime(
                user_id=user.id,
                service_id=service.id,
                date=service.date,
                hours=hours,
                overtime_type=ot_type,
                hourly_rate=rate,
                amount=amount,
                is_paid=False
            )
            db.add(overtime)
    
    # 2. Calculate allowances
    allowances, allowances_total = calculate_service_allowances(service, user)
    calculations['allowances'] = allowances
    
    # 3. Calculate mission/escort compensation
    mission_total = 0
    if service.service_type == "ESCORT":
        escort_comp, escort_total = calculate_escort_compensation(service)
        calculations['mission'] = escort_comp
        mission_total = escort_total
    elif service.service_type == "MISSION":
        mission_comp, mission_total_calc = calculate_mission_compensation(service)
        calculations['mission'] = mission_comp
        mission_total = mission_total_calc
    
    # 4. Calculate totals
    total = overtime_total + allowances_total + mission_total
    
    calculations['totals'] = {
        'overtime': overtime_total,
        'allowances': allowances_total,
        'mission': mission_total,
        'total': total
    }
    
    # Update service
    service.overtime_amount = overtime_total
    service.allowances_amount = allowances_total
    service.mission_amount = mission_total
    service.total_amount = total
    service.calculation_details = calculations
    
    return calculations

def calculate_month_totals(db: Session, user_id: int, month: int, year: int):
    """Calculate month totals for dashboard"""
    # Get all services for the month
    services = db.query(Service).filter(
        Service.user_id == user_id,
        db.extract('month', Service.date) == month,
        db.extract('year', Service.date) == year
    ).all()
    
    # Get paid overtime for the month
    paid_overtime = db.query(Overtime).filter(
        Overtime.user_id == user_id,
        Overtime.is_paid == True,
        Overtime.payment_month == f"{year}-{month:02d}"
    ).all()
    
    # Calculate totals
    data = {
        'days_worked': len(services),
        'total_hours': sum(s.total_hours for s in services),
        'paid_overtime': sum(ot.amount for ot in paid_overtime),
        'paid_hours': sum(ot.hours for ot in paid_overtime),
        'unpaid_overtime': 0,
        'unpaid_hours': 0,
        'allowances': sum(s.allowances_amount for s in services),
        'missions': sum(s.mission_amount for s in services),
        'total': 0
    }
    
    # Get unpaid overtime for this month's services
    for service in services:
        unpaid_ot = db.query(Overtime).filter(
            Overtime.service_id == service.id,
            Overtime.is_paid == False
        ).all()
        data['unpaid_overtime'] += sum(ot.amount for ot in unpaid_ot)
        data['unpaid_hours'] += sum(ot.hours for ot in unpaid_ot)
    
    # Calculate total (paid amounts only)
    data['total'] = data['paid_overtime'] + data['allowances'] + data['missions']
    
    return data