"""
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

async def new_service_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start new service registration"""
    # Clear user data
    context.user_data.clear()
    
    # Check if escort was pre-selected
    if context.user_data.get('service_type') == 'ESCORT':
        context.user_data['preselected_escort'] = True
    
    await update.callback_query.answer() if update.callback_query else None
    
    text = "📅 <b>NUOVO SERVIZIO</b>\n\nQuando hai lavorato?\n👇 Seleziona:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, 
            parse_mode='HTML',
            reply_markup=get_date_keyboard("service_date")
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode='HTML', 
            reply_markup=get_date_keyboard("service_date")
        )
    
    return SELECT_DATE

async def handle_date_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle date selection"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.replace("service_date_", "")
    
    if action == "today":
        service_date = datetime.now().date()
    elif action == "yesterday":
        service_date = datetime.now().date() - timedelta(days=1)
    else:
        # Ask for manual date input
        await query.edit_message_text(
            "📅 Inserisci la data del servizio (formato: GG/MM/AAAA):",
            parse_mode='HTML'
        )
        return SELECT_DATE
    
    context.user_data['service_date'] = service_date
    
    # Check if holiday/super-holiday
    is_holiday_day = is_holiday(service_date)
    is_super = is_super_holiday(service_date)
    
    date_str = format_date(service_date)
    if is_super:
        date_str += " (🎄 SUPER-FESTIVO)"
    elif is_holiday_day:
        date_str += " (🔴 Festivo)"
    
    # Check user status for that day
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == str(query.from_user.id)).first()
        
        # Check if user was on leave
        # TODO: Check leave records
        
        text = f"📅 Data: <b>{date_str}</b>\n\n"
        text += "⚠️ <b>STATO PERSONALE</b> per questa data:\n"
        
        keyboard = [
            [InlineKeyboardButton("🟢 In servizio ordinario", callback_data="status_normal")],
            [InlineKeyboardButton("🏖️ In LICENZA", callback_data="status_leave")],
            [InlineKeyboardButton("🔄 Riposo settimanale", callback_data="status_rest")],
            [InlineKeyboardButton("⏰ Recupero ore", callback_data="status_recovery")],
            [InlineKeyboardButton("📋 Altro permesso", callback_data="status_other")]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    finally:
        db.close()
    
    return SELECT_TIME

async def handle_status_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle personal status selection"""
    query = update.callback_query
    await query.answer()
    
    status = query.data.replace("status_", "")
    context.user_data['personal_status'] = status
    
    if status in ['leave', 'rest']:
        context.user_data['called_from_leave'] = (status == 'leave')
        context.user_data['called_from_rest'] = (status == 'rest')
        
        text = "⚠️ <b>RICHIAMO IN SERVIZIO!</b>\n"
        text += "✅ Compensazione €10,90 applicata\n"
        if status == 'leave':
            text += "✅ Licenza scalata automaticamente\n"
    else:
        text = ""
    
    text += "\n⏰ <b>ORARIO SERVIZIO</b>\n\n"
    text += "Inserisci l'orario di inizio (formato HH:MM):\n"
    text += "Esempi: 06:30, 14:45, 22:00"
    
    await query.edit_message_text(text, parse_mode='HTML')
    context.user_data['waiting_for_start_time'] = True
    
    return SELECT_TIME

async def handle_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start time selection"""
    query = update.callback_query
    await query.answer()
    
    hour = int(query.data.replace("start_time_", ""))
    service_date = context.user_data['service_date']
    start_time = datetime.combine(service_date, time(hour, 0))
    context.user_data['start_time'] = start_time
    
    text = f"⏰ Inizio: <b>{hour:02d}:00</b>\n\nOra di fine?"
    
    # Calculate available end hours (same day or next)
    end_hours = list(range(hour + 1, 24)) + list(range(0, 24))
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=get_time_keyboard(hour_range=end_hours, prefix="end_time")
    )
    
    return SELECT_SERVICE_TYPE

async def handle_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle end time selection"""
    query = update.callback_query
    await query.answer()
    
    hour = int(query.data.replace("end_time_", ""))
    start_time = context.user_data['start_time']
    
    # Calculate end time (might be next day)
    if hour <= start_time.hour:
        # Next day
        end_date = start_time.date() + timedelta(days=1)
    else:
        end_date = start_time.date()
    
    end_time = datetime.combine(end_date, time(hour, 0))
    context.user_data['end_time'] = end_time
    
    # Calculate total hours
    total_hours = (end_time - start_time).total_seconds() / 3600
    context.user_data['total_hours'] = total_hours
    
    # Check for double shift
    is_double = total_hours > 12
    context.user_data['is_double_shift'] = is_double
    
    text = f"⏰ <b>ORARIO COMPLETO</b>\n\n"
    text += f"Dalle: {start_time.strftime('%H:%M')} "
    text += f"Alle: {end_time.strftime('%H:%M')}\n\n"
    text += f"✅ Totale: <b>{total_hours:.0f} ore</b>\n"
    
    if context.user_data.get('personal_status') == 'recovery':
        # Ask about recovery hours
        text += "\n⏰ <b>RECUPERO ORE</b>\n"
        text += "Quante ore stai recuperando? (le restanti saranno straordinario)\n"
        text += "Inserisci il numero di ore:"
        
        await query.edit_message_text(text, parse_mode='HTML')
        return SELECT_SERVICE_TYPE
    
    if is_double:
        text += "\n⚠️ <b>DOPPIA TURNAZIONE RILEVATA!</b>\n\n"
        text += f"Servizio di {total_hours:.0f} ore = 2 turni esterni\n\n"
        text += "✅ Applicati automaticamente:\n"
        text += "├ 1° turno esterno: €5,45\n"
        text += "├ 2° turno esterno: €5,45\n"
        text += "└ Totale: €10,90\n"
    
    # Check if escort was pre-selected
    if context.user_data.get('preselected_escort'):
        context.user_data['service_type'] = ServiceType.ESCORT
        return await ask_escort_details(update, context)
    
    text += "\n\nTipo di servizio?"
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=get_service_type_keyboard()
    )
    
    return SELECT_SERVICE_TYPE

async def handle_recovery_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle recovery hours input"""
    try:
        recovery_hours = float(update.message.text)
        total_hours = context.user_data['total_hours']
        
        if recovery_hours > total_hours:
            await update.message.reply_text(
                "❌ Le ore di recupero non possono superare le ore totali!",
                parse_mode='HTML'
            )
            return SELECT_SERVICE_TYPE
        
        context.user_data['recovery_hours'] = recovery_hours
        overtime_hours = total_hours - recovery_hours
        
        text = f"✅ <b>RECUPERO REGISTRATO</b>\n\n"
        text += f"├ Ore recuperate: {recovery_hours:.0f}h\n"
        text += f"├ Straordinario nuovo: {overtime_hours:.0f}h\n"
        text += f"└ ✅ Recupero registrato\n\n"
        
        # Check if escort was pre-selected
        if context.user_data.get('preselected_escort'):
            context.user_data['service_type'] = ServiceType.ESCORT
            return await ask_escort_details(update, context)
        
        text += "Tipo di servizio?"
        
        await update.message.reply_text(
            text,
            parse_mode='HTML',
            reply_markup=get_service_type_keyboard()
        )
        
    except ValueError:
        await update.message.reply_text(
            "❌ Inserisci un numero valido di ore!",
            parse_mode='HTML'
        )
    
    return SELECT_SERVICE_TYPE

async def handle_service_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle service type selection"""
    query = update.callback_query
    await query.answer()
    
    service_type = ServiceType(query.data.replace("service_type_", ""))
    context.user_data['service_type'] = service_type
    
    if service_type == ServiceType.ESCORT:
        return await ask_escort_details(update, context)
    elif service_type == ServiceType.MISSION:
        return await ask_mission_details(update, context)
    else:
        # Local service - go to confirmation
        return await show_service_summary(update, context)

async def ask_escort_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for escort details"""
    text = "🚔 <b>DETTAGLI SCORTA</b>\n\n"
    text += "📝 Numero Foglio Viaggio:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')
    
    return TRAVEL_DETAILS

async def handle_travel_sheet_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle travel sheet number input"""
    context.user_data['travel_sheet_number'] = update.message.text
    
    await update.message.reply_text(
        "📍 Destinazione:",
        parse_mode='HTML'
    )
    
    return TRAVEL_TYPE

async def handle_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle destination input"""
    context.user_data['destination'] = update.message.text
    
    # Ask for detailed timing
    text = "⏱️ <b>TIMING DETTAGLIATO</b>\n\n"
    text += "Inserisci gli orari nel formato HH:MM\n\n"
    text += "<b>1️⃣ ANDATA (senza VIP):</b>\n"
    text += "Ora partenza dalla sede:"
    
    await update.message.reply_text(text, parse_mode='HTML')
    
    context.user_data['escort_phase'] = 'departure_time'
    return TRAVEL_TYPE

async def handle_escort_timing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle escort timing details"""
    phase = context.user_data.get('escort_phase')
    
    try:
        # Parse time input
        time_parts = update.message.text.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        if phase == 'departure_time':
            context.user_data['departure_time'] = (hour, minute)
            await update.message.reply_text(
                "Ora arrivo a destinazione:",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'arrival_time'
            
        elif phase == 'arrival_time':
            context.user_data['arrival_time'] = (hour, minute)
            await update.message.reply_text(
                "<b>2️⃣ SERVIZIO CON VIP:</b>\n"
                "Ora ritiro VIP:",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'vip_pickup'
            
        elif phase == 'vip_pickup':
            context.user_data['vip_pickup'] = (hour, minute)
            await update.message.reply_text(
                "Ora fine servizio con VIP:",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'vip_end'
            
        elif phase == 'vip_end':
            context.user_data['vip_end'] = (hour, minute)
            await update.message.reply_text(
                "<b>3️⃣ RITORNO (senza VIP):</b>\n"
                "Ora partenza per il rientro:",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'return_departure'
            
        elif phase == 'return_departure':
            context.user_data['return_departure'] = (hour, minute)
            await update.message.reply_text(
                "Ora rientro in sede:",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'return_arrival'
            
        elif phase == 'return_arrival':
            context.user_data['return_arrival'] = (hour, minute)
            
            # Calculate active/passive hours
            calculate_escort_hours(context)
            
            # Ask for kilometers
            await update.message.reply_text(
                "🚗 Chilometri totali (andata e ritorno):",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'km'
            
        elif phase == 'km':
            context.user_data['km_total'] = int(update.message.text)
            
            # Ask for mission type
            text = "💶 <b>REGIME DI RIMBORSO</b>\n\n"
            text += "Scegli come essere pagato:"
            
            await update.message.reply_text(
                text,
                parse_mode='HTML',
                reply_markup=get_mission_type_keyboard()
            )
            return MEAL_DETAILS
            
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Formato non valido! Usa HH:MM (es: 08:30)",
            parse_mode='HTML'
        )
    
    return TRAVEL_TYPE

def calculate_escort_hours(context):
    """Calculate active and passive travel hours"""
    service_date = context.user_data['service_date']
    
    # Parse times
    dep_h, dep_m = context.user_data['departure_time']
    arr_h, arr_m = context.user_data['arrival_time']
    vip_start_h, vip_start_m = context.user_data['vip_pickup']
    vip_end_h, vip_end_m = context.user_data['vip_end']
    ret_dep_h, ret_dep_m = context.user_data['return_departure']
    ret_arr_h, ret_arr_m = context.user_data['return_arrival']
    
    # Create datetime objects
    departure = datetime.combine(service_date, time(dep_h, dep_m))
    arrival = datetime.combine(service_date, time(arr_h, arr_m))
    vip_start = datetime.combine(service_date, time(vip_start_h, vip_start_m))
    vip_end = datetime.combine(service_date, time(vip_end_h, vip_end_m))
    return_dep = datetime.combine(service_date, time(ret_dep_h, ret_dep_m))
    return_arr = datetime.combine(service_date, time(ret_arr_h, ret_arr_m))
    
    # Handle day crossing
    if arrival < departure:
        arrival += timedelta(days=1)
    if vip_start < arrival:
        vip_start = arrival  # VIP pickup can't be before arrival
    if vip_end < vip_start:
        vip_end += timedelta(days=1)
    if return_dep < vip_end:
        return_dep = vip_end  # Return can't start before VIP service ends
    if return_arr < return_dep:
        return_arr += timedelta(days=1)
    
    # Calculate hours
    active_hours = (arrival - departure).total_seconds() / 3600
    active_hours += (return_arr - return_dep).total_seconds() / 3600
    
    passive_hours = (vip_end - vip_start).total_seconds() / 3600
    
    context.user_data['active_travel_hours'] = active_hours
    context.user_data['passive_travel_hours'] = passive_hours

async def ask_mission_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for mission details"""
    text = "✈️ <b>DETTAGLI MISSIONE</b>\n\n"
    text += "📍 Destinazione:"
    
    await update.callback_query.edit_message_text(text, parse_mode='HTML')
    
    return SERVICE_DETAILS

async def handle_mission_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mission destination"""
    context.user_data['destination'] = update.message.text
    
    await update.message.reply_text(
        "🚗 Chilometri totali (se applicabile, altrimenti 0):",
        parse_mode='HTML'
    )
    
    return TRAVEL_TYPE

async def handle_mission_km(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mission kilometers"""
    try:
        km = int(update.message.text)
        context.user_data['km_total'] = km
        
        # Ask for payment type
        text = "💶 <b>REGIME DI RIMBORSO</b>\n\n"
        text += "Scegli come essere pagato:"
        
        # TODO: Add automatic comparison
        
        await update.message.reply_text(
            text,
            parse_mode='HTML',
            reply_markup=get_mission_type_keyboard()
        )
        
        return MEAL_DETAILS
        
    except ValueError:
        await update.message.reply_text(
            "❌ Inserisci un numero valido!",
            parse_mode='HTML'
        )
        return TRAVEL_TYPE

async def handle_mission_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mission payment type selection"""
    query = update.callback_query
    await query.answer()
    
    mission_type = query.data.replace("mission_type_", "").upper()
    context.user_data['mission_type'] = mission_type
    
    if mission_type == "FORFEIT":
        # Forfeit doesn't need meal details
        return await show_service_summary(update, context)
    else:
        # Ask about meals
        total_hours = context.user_data['total_hours']
        meals_entitled = 0
        
        if total_hours >= 8:
            meals_entitled = 1
        if total_hours >= 12:
            meals_entitled = 2
        
        text = f"🍽️ <b>PASTI DURANTE IL SERVIZIO</b>\n\n"
        text += f"Servizio di {total_hours:.0f} ore = Diritto a {meals_entitled} pasti\n\n"
        text += "Pasti consumati:"
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=get_meal_keyboard()
        )
        
        return CONFIRM_SERVICE

async def handle_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle meal selection"""
    query = update.callback_query
    await query.answer()
    
    meals = int(query.data.replace("meals_", ""))
    context.user_data['meals_consumed'] = meals
    
    # Calculate meal reimbursement
    total_hours = context.user_data['total_hours']
    meals_entitled = 2 if total_hours >= 12 else (1 if total_hours >= 8 else 0)
    meals_not_consumed = meals_entitled - meals
    
    if meals_not_consumed > 0 and meals_entitled > 0:
        # Ask which meals were not consumed
        text = "Quali pasti NON sono stati consumati?\n"
        
        keyboard = []
        if meals_not_consumed >= 1:
            keyboard.append([InlineKeyboardButton("☐ Pranzo", callback_data="meal_lunch")])
        if meals_not_consumed >= 2:
            keyboard.append([InlineKeyboardButton("☐ Cena", callback_data="meal_dinner")])
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CONFIRM_SERVICE
    else:
        return await show_service_summary(update, context)

async def show_service_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show service summary for confirmation"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            User.telegram_id == str(update.effective_user.id)
        ).first()
        
        # Create service object
        service = Service(
            user_id=user.id,
            date=context.user_data['service_date'],
            start_time=context.user_data['start_time'],
            end_time=context.user_data['end_time'],
            total_hours=context.user_data['total_hours'],
            service_type=context.user_data['service_type'],
            is_holiday=is_holiday(context.user_data['service_date']),
            is_super_holiday=is_super_holiday(context.user_data['service_date']),
            is_double_shift=context.user_data.get('is_double_shift', False),
            called_from_leave=context.user_data.get('called_from_leave', False),
            called_from_rest=context.user_data.get('called_from_rest', False),
            recovery_hours=context.user_data.get('recovery_hours', 0),
            travel_sheet_number=context.user_data.get('travel_sheet_number'),
            destination=context.user_data.get('destination'),
            km_total=context.user_data.get('km_total', 0),
            active_travel_hours=context.user_data.get('active_travel_hours', 0),
            passive_travel_hours=context.user_data.get('passive_travel_hours', 0),
            mission_type=context.user_data.get('mission_type', 'ORDINARY'),
            meals_consumed=context.user_data.get('meals_consumed', 0)
        )
        
        # Calculate totals
        calculations = calculate_service_total(db, user, service)
        
        # Format summary
        text = format_detailed_summary(service, calculations)
        
        # Store service in context for saving
        context.user_data['service'] = service
        context.user_data['calculations'] = calculations
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=get_confirm_keyboard()
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode='HTML',
                reply_markup=get_confirm_keyboard()
            )
        
    finally:
        db.close()
    
    return ConversationHandler.END

def format_detailed_summary(service, calculations):
    """Format detailed service summary"""
    text = f"💰 <b>RIEPILOGO SERVIZIO</b>\n"
    text += f"{format_date(service.date)}"
    
    if service.is_super_holiday:
        text += " - SUPER-FESTIVO"
    elif service.is_holiday:
        text += " - Festivo"
    
    text += f" ({service.total_hours:.0f} ore)\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    # Service details
    if service.service_type == ServiceType.ESCORT:
        text += f"🚔 SCORTA {service.destination} (F.V. {service.travel_sheet_number})\n"
    elif service.service_type == ServiceType.LOCAL:
        text += "📍 SERVIZIO LOCALE\n"
    else:
        text += f"✈️ MISSIONE {service.destination}\n"
    
    text += f"Servizio: {format_time_range(service.start_time, service.end_time)} "
    text += f"({service.total_hours:.0f} ore)\n"
    
    if service.called_from_leave:
        text += "📍 RICHIAMATO DA LICENZA\n"
    elif service.called_from_rest:
        text += "📍 RICHIAMATO DA RIPOSO\n"
    
    # Overtime breakdown
    if calculations['overtime']:
        text += "\n<b>1️⃣ STRAORDINARI</b>\n"
        
        for ot_type, details in calculations['overtime'].items():
            text += f"├ {ot_type}: {details['hours']:.1f}h × "
            text += f"{format_currency(details['rate'])} = "
            text += f"{format_currency(details['amount'])}\n"
        
        text += f"└ Subtotale: {format_currency(calculations['totals']['overtime'])}\n"
    
    # Allowances
    if calculations['allowances']:
        text += "\n<b>2️⃣ INDENNITÀ GIORNALIERE</b>\n"
        
        allowance_names = {
            'external_service': 'Servizio esterno (1°)',
            'external_service_2': 'Servizio esterno (2°)',
            'super_holiday_presence': 'Presenza SUPER-festiva',
            'holiday_presence': 'Presenza festiva',
            'compensation': 'COMPENSAZIONE',
            'territory_control_evening': 'Controllo territorio serale',
            'territory_control_night': 'Controllo territorio notturno'
        }
        
        for key, amount in calculations['allowances'].items():
            name = allowance_names.get(key, key)
            text += f"├ {name}: {format_currency(amount)}\n"
        
        text += f"└ Subtotale: {format_currency(calculations['totals']['allowances'])}\n"
    
    # Mission compensation
    if calculations['mission']:
        if service.mission_type == "FORFEIT":
            text += f"\n<b>3️⃣ MISSIONE (Regime: FORFETTARIO)</b>\n"
        else:
            text += f"\n<b>3️⃣ MISSIONE (Regime: ORDINARIO)</b>\n"
        
        for key, amount in calculations['mission'].items():
            if key == 'km':
                text += f"├ Km ({service.km_total} A/R): {format_currency(amount)}\n"
            elif key == 'forfeit_24h':
                text += f"├ Forfettario <24h: {format_currency(amount)} (NETTO)\n"
            elif key == 'active_travel':
                hours = service.active_travel_hours
                text += f"├ Viaggio attivo: {hours:.1f}h = {format_currency(amount)}\n"
            else:
                text += f"├ {key}: {format_currency(amount)}\n"
        
        text += f"└ Subtotale: {format_currency(calculations['totals']['mission'])}\n"
    
    # Total
    text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    text += f"💶 <b>TOTALE GIORNATA: {format_currency(calculations['totals']['total'])}</b>\n"
    
    return text

async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle service confirmation"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.replace("confirm_", "")
    
    if action == "yes":
        # Save service
        db = SessionLocal()
        try:
            service = context.user_data['service']
            db.add(service)
            
            # Create travel sheet if escort
            if service.service_type == ServiceType.ESCORT and service.travel_sheet_number:
                travel_sheet = TravelSheet(
                    user_id=service.user_id,
                    service_id=service.id,
                    sheet_number=service.travel_sheet_number,
                    date=service.date,
                    destination=service.destination,
                    amount=service.mission_amount + (service.km_total * 0.35)
                )
                db.add(travel_sheet)
            
            # Update user leaves if called from leave
            if service.called_from_leave:
                user = db.query(User).filter(User.id == service.user_id).first()
                user.current_year_leave_used += 1
            
            db.commit()
            
            await query.edit_message_text(
                "✅ <b>Servizio salvato con successo!</b>\n\n"
                "Usa /start per tornare al menu principale.",
                parse_mode='HTML'
            )
            
        finally:
            db.close()
    
    elif action == "no":
        await query.edit_message_text(
            "❌ Registrazione annullata.\n\n"
            "Usa /start per tornare al menu principale.",
            parse_mode='HTML'
        )
    
    elif action == "edit":
        # Restart conversation
        return await new_service_command(update, context)
    
    return ConversationHandler.END

# Create conversation handler
service_conversation_handler = ConversationHandler(
    entry_points=[
        CommandHandler("nuovo", new_service_command),
        CommandHandler("scorta", new_service_command),
        CallbackQueryHandler(new_service_command, pattern="^dashboard_new_")
    ],
    states={
        SELECT_DATE: [
            CallbackQueryHandler(handle_date_selection, pattern="^service_date_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_date_selection)
        ],
        
        SELECT_TIME: [
            CallbackQueryHandler(handle_status_selection, pattern="^status_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_input)
        ],
        SELECT_SERVICE_TYPE: [
            CallbackQueryHandler(handle_service_type, pattern="^service_type_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_input)
        ],
        SERVICE_DETAILS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mission_destination)
        ],
        TRAVEL_DETAILS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_travel_sheet_number)
        ],
        TRAVEL_TYPE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_escort_timing),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mission_km)
        ],
        MEAL_DETAILS: [
            CallbackQueryHandler(handle_mission_type, pattern="^mission_type_")
        ],
        CONFIRM_SERVICE: [
            CallbackQueryHandler(handle_meals, pattern="^meals_"),
            CallbackQueryHandler(handle_confirmation, pattern="^confirm_")
        ]
    },
    fallbacks=[CommandHandler("start", start_command)]
)