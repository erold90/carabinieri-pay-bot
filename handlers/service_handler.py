"""
Service registration handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime, timedelta, time, date
from sqlalchemy.orm import Session

from database.connection import SessionLocal, get_db
from database.models import User, Service, ServiceType, TravelSheet
from config.settings import (
    SELECT_DATE, SELECT_TIME, SELECT_SERVICE_TYPE, SERVICE_DETAILS,
    TRAVEL_DETAILS, TRAVEL_TYPE, MEAL_DETAILS, CONFIRM_SERVICE
)
from config.constants import SUPER_HOLIDAYS, OVERTIME_RATES, MEAL_RATES
from utils.keyboards import (
    get_date_keyboard, get_time_keyboard, get_service_type_keyboard,
    get_yes_no_keyboard, get_mission_type_keyboard, get_meal_keyboard,
    get_confirm_keyboard
)
from utils.formatters import format_currency, format_date, format_time_range, format_hours
from utils.validators import validate_time_input
from services.calculation_service import (
    is_holiday, is_super_holiday, calculate_service_total
)
from handlers.start_handler import start_command

from database.connection import SessionLocal, get_db
from database.models import User, Service, ServiceType, TravelSheet
from utils.validators import validate_time_input
from config.settings import (
    SELECT_DATE, SELECT_TIME, SELECT_SERVICE_TYPE, SERVICE_DETAILS,
    TRAVEL_DETAILS, TRAVEL_TYPE, MEAL_DETAILS, CONFIRM_SERVICE
)
from config.constants import SUPER_HOLIDAYS, OVERTIME_RATES, MEAL_RATES
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


async def handle_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual date input"""
    text = update.message.text.strip()
    
    try:
        # Parse date in format GG/MM/AAAA
        parts = text.split('/')
        if len(parts) == 3:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            service_date = date(year, month, day)
            
            # Validate date
            if service_date > datetime.now().date() + timedelta(days=7):
                await update.message.reply_text(
                    "❌ Non puoi inserire servizi futuri oltre 7 giorni!",
                    parse_mode='HTML'
                )
                return SELECT_DATE
            
            context.user_data['service_date'] = service_date
            
            # Check if holiday
            is_holiday_day = is_holiday(service_date)
            is_super = is_super_holiday(service_date)
            
            date_str = format_date(service_date)
            if is_super:
                date_str += " (🎄 SUPER-FESTIVO)"
            elif is_holiday_day:
                date_str += " (🔴 Festivo)"
            
            # Ask for status
            text = f"📅 Data: <b>{date_str}</b>\n\n"
            text += "⚠️ <b>STATO PERSONALE</b> per questa data:\n"
            
            keyboard = [
                [InlineKeyboardButton("🟢 In servizio ordinario", callback_data="status_normal")],
                [InlineKeyboardButton("🏖️ In LICENZA", callback_data="status_leave")],
                [InlineKeyboardButton("🔄 Riposo settimanale", callback_data="status_rest")],
                [InlineKeyboardButton("⏰ Recupero ore", callback_data="status_recovery")],
                [InlineKeyboardButton("📋 Altro permesso", callback_data="status_other")]
            ]
            
            await update.message.reply_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            return SELECT_TIME
            
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Formato data non valido!\n\n"
            "Usa il formato: GG/MM/AAAA\n"
            "Esempio: 25/05/2024",
            parse_mode='HTML'
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
    with get_db() as db:
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
    
    context.user_data['waiting_for_destination'] = True
    return TRAVEL_TYPE

async def handle_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle destination input"""
    if not context.user_data.get('waiting_for_destination'):
        return TRAVEL_TYPE
        
    context.user_data['destination'] = update.message.text
    context.user_data['waiting_for_destination'] = False
    
    # Controlla se siamo in un servizio di scorta o missione
    service_type = context.user_data.get('service_type')
    
    if service_type == ServiceType.ESCORT:
        # Per scorta, chiedi il timing dettagliato
        text = "⏱️ <b>ORARI SERVIZIO</b>\n\n"
        text += "Ora partenza dalla sede (HH:MM):"
        text += "Inserisci gli orari nel formato HH:MM\n\n"
        text += "<b>1️⃣ ANDATA (senza VIP):</b>\n"
        text += "Ora partenza dalla sede:"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
        context.user_data['escort_phase'] = 'departure_time'
        context.user_data['waiting_for_escort_timing'] = True
        return TRAVEL_TYPE
    else:
        # Per missione, chiedi i km
        await update.message.reply_text(
            "🚗 Chilometri totali (se applicabile, altrimenti 0):",
            parse_mode='HTML'
        )
        
        context.user_data['waiting_for_km'] = True
        return TRAVEL_TYPE

async def handle_escort_timing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle escort timing details - versione semplificata"""
    if not context.user_data.get('waiting_for_escort_timing'):
        return TRAVEL_TYPE
        
    phase = context.user_data.get('escort_phase')
    if not phase:
        return TRAVEL_TYPE
    
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
            # Assume che il VIP viene preso all'arrivo
            context.user_data['vip_pickup'] = (hour, minute)
            
            await update.message.reply_text(
                "Ora partenza per il rientro:",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'return_departure'
            
        elif phase == 'return_departure':
            context.user_data['return_departure'] = (hour, minute)
            # Assume che il VIP viene lasciato alla partenza per il rientro
            context.user_data['vip_end'] = (hour, minute)
            
            await update.message.reply_text(
                "Ora rientro in sede:",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'return_arrival'
            
        elif phase == 'return_arrival':
            context.user_data['return_arrival'] = (hour, minute)
            
            # Calcola ore attive/passive automaticamente
            calculate_escort_hours(context)
            
            # Chiedi tipo di pagamento missione
            text = "💶 <b>REGIME DI RIMBORSO</b>\n\n"
            text += "Scegli come essere pagato:"
            
            await update.message.reply_text(
                text,
                parse_mode='HTML',
                reply_markup=get_mission_type_keyboard()
            )
            
            context.user_data['escort_phase'] = None
            context.user_data['waiting_for_escort_timing'] = False
            return MEAL_DETAILS
            
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Formato non valido! Usa HH:MM (es: 08:30)",
            parse_mode='HTML'
        )
    
    return TRAVEL_TYPE


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
        # Per forfettario, chiedi se continua il giorno dopo
        text = "💰 <b>REGIME FORFETTARIO</b>\n\n"
        text += "Il servizio continua anche domani?\n\n"
        text += "📌 Info: €110 netti/24h + €50 per 12-24h extra"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Sì, continua", callback_data="forfeit_continues_yes"),
                InlineKeyboardButton("❌ No, termina oggi", callback_data="forfeit_continues_no")
            ]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CONFIRM_SERVICE
    else:
        # Ask about meals for ordinary
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
    
    # Handle both numeric meals and confirm
    if query.data == "meal_confirm":
        # User confirmed meal selection
        return await show_service_summary(update, context)
    
    try:
        meals = int(query.data.replace("meals_", ""))
    except ValueError:
        # Not a number, handle meal selection
        return await handle_meal_selection(update, context)
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
    with get_db() as db:
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
        
                
        # Traduzioni tipi straordinario
        type_names = {
            'WEEKDAY_DAY': 'Feriale Diurno',
            'WEEKDAY_NIGHT': 'Feriale Notturno',
            'HOLIDAY_DAY': 'Festivo Diurno',
            'HOLIDAY_NIGHT': 'Festivo Notturno'
        }
        
        for ot_type, details in calculations['overtime'].items():
            text += f"├ {type_names.get(ot_type, ot_type)}: {details['hours']:.1f}h × "
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
        
        # Mostra dettagli pasti se applicabile
        if service.service_type in [ServiceType.ESCORT, ServiceType.MISSION]:
            meals_entitled = 0
            if service.total_hours >= 8:
                meals_entitled = 1
            if service.total_hours >= 12:
                meals_entitled = 2
            
            if meals_entitled > 0:
                meals_consumed = service.meals_consumed or 0
                meals_not_consumed = meals_entitled - meals_consumed
                
                text += f"\n🍽️ <b>PASTI:</b>\n"
                text += f"├ Diritto a {meals_entitled} pasti (servizio {service.total_hours:.0f}h)\n"
                text += f"├ Consumati: {meals_consumed}\n"
                text += f"├ NON consumati: {meals_not_consumed}\n"
                
                if 'meal_reimbursement' in calculations['mission']:
                    text += f"└ Rimborso: {format_currency(calculations['mission']['meal_reimbursement'])}\n"
        
        
        
        # Traduzioni chiavi missione
        mission_names = {
            'km': 'Chilometri',
            'forfeit_24h': 'Forfettario 24h',
            'forfeit': 'Forfettario',
            'active_travel': 'Maggiorazione viaggio',
            'hourly_allowance': 'Indennità oraria',
            'daily_allowance': 'Diaria giornaliera',
            'km_reimbursement': 'Rimborso chilometrico',
            'meal_reimbursement': 'Rimborso pasti'
        }
        
        for key, amount in calculations['mission'].items():
            if key == 'km':
                text += f"├ Km ({service.km_total} A/R): {format_currency(amount)}\n"
            elif key == 'forfeit_24h':
                text += f"├ Forfettario <24h: {format_currency(amount)} (NETTO)\n"
            elif key == 'active_travel':
                hours = service.active_travel_hours
                text += f"├ Viaggio attivo: {hours:.1f}h = {format_currency(amount)}\n"
            else:
                text += f"├ {mission_names.get(key, key)}: {format_currency(amount)}\n"
        
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
        with get_db() as db:
            service = context.user_data['service']
            
            # Verifica dati prima del salvataggio
            print(f"[DEBUG] Salvataggio servizio:")
            print(f"  - Data: {service.date}")
            print(f"  - Orario: {service.start_time} - {service.end_time}")
            print(f"  - Tipo: {service.service_type}")
            print(f"  - FV: {service.travel_sheet_number}")
            print(f"  - Destinazione: {service.destination}")
            print(f"  - Km: {service.km_total}")

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


async def handle_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Handle manual time input from user"""
   text = update.message.text.strip()
   
   # Parse time in various formats: HH:MM, HH.MM, HHMM, H:MM
   time_patterns = [
       r'^(\d{1,2}):(\d{2})$',     # HH:MM or H:MM
       r'^(\d{1,2})\.(\d{2})$',     # HH.MM or H.MM
       r'^(\d{2})(\d{2})$',         # HHMM
       r'^(\d{1,2})$'               # Just hour
   ]
   
   hour = None
   minute = 0
   
   for pattern in time_patterns:
       match = re.match(pattern, text)
       if match:
           if len(match.groups()) == 2:
               hour = int(match.group(1))
               minute = int(match.group(2))
           else:
               hour = int(match.group(1))
               minute = 0
           break
   
   if hour is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
       # Valid time
       if context.user_data.get('waiting_for_start_time'):
           service_date = context.user_data['service_date']
           start_time = datetime.combine(service_date, time(hour, minute))
           context.user_data['start_time'] = start_time
           context.user_data['waiting_for_start_time'] = False
           
           text = f"⏰ Inizio: <b>{hour:02d}:{minute:02d}</b>\n\n"
           text += "Inserisci l'orario di fine (formato HH:MM):\n"
           text += "Esempi: 14:30, 22:00, 2:30"
           
           await update.message.reply_text(text, parse_mode='HTML')
           context.user_data['waiting_for_end_time'] = True
           return SELECT_TIME
           
       elif context.user_data.get('waiting_for_end_time'):
           start_time = context.user_data['start_time']
           service_date = context.user_data['service_date']
           
           # Calculate end time (might be next day)
           if hour < start_time.hour or (hour == start_time.hour and minute <= start_time.minute):
               # Next day
               end_date = service_date + timedelta(days=1)
           else:
               end_date = service_date
           
           end_time = datetime.combine(end_date, time(hour, minute))
           context.user_data['end_time'] = end_time
           context.user_data['waiting_for_end_time'] = False
           
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
           
           await update.message.reply_text(
               text,
               parse_mode='HTML',
               reply_markup=get_service_type_keyboard()
           )
           
           return SELECT_SERVICE_TYPE
           
   else:
       await update.message.reply_text(
           "❌ Orario non valido! Usa il formato HH:MM\n"
           "Esempi validi: 08:30, 14:45, 22:00, 8:30",
           parse_mode='HTML'
       )
       return SELECT_TIME

def calculate_escort_hours(context):
    """Calcola automaticamente ore attive e passive per scorte"""
    user_data = context.user_data
    
    # Recupera i tempi salvati
    departure = user_data.get('departure_time', (0, 0))
    arrival = user_data.get('arrival_time', (0, 0))
    return_departure = user_data.get('return_departure', (0, 0))
    return_arrival = user_data.get('return_arrival', (0, 0))
    
    # Calcola ore viaggio attivo (senza VIP)
    active_hours = 0.0
    
    # Andata
    if arrival[0] >= departure[0]:
        active_hours += (arrival[0] - departure[0]) + (arrival[1] - departure[1]) / 60
    else:
        active_hours += (24 - departure[0] + arrival[0]) + (arrival[1] - departure[1]) / 60
    
    # Ritorno (dopo aver lasciato VIP)
    if return_arrival[0] >= return_departure[0]:
        active_hours += (return_arrival[0] - return_departure[0]) + (return_arrival[1] - return_departure[1]) / 60
    else:
        active_hours += (24 - return_departure[0] + return_arrival[0]) + (return_arrival[1] - return_departure[1]) / 60
    
    active_hours = round(active_hours, 1)
    
    # Ore passive
    total_hours = user_data.get('total_hours', 0)
    overtime_hours = max(0, total_hours - 6)  # 6 ore base
    passive_hours = round(max(0, overtime_hours - active_hours), 1)
    
    # Salva nel context
    user_data['active_travel_hours'] = active_hours
    user_data['passive_travel_hours'] = passive_hours
    
    return active_hours, passive_hours




async def handle_travel_type_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inputs in TRAVEL_TYPE state"""
    text = update.message.text
    
    # Se stiamo aspettando la destinazione
    if context.user_data.get('waiting_for_destination'):
        return await handle_destination(update, context)
    
    # Se stiamo aspettando timing escort
    elif context.user_data.get('waiting_for_escort_timing'):
        return await handle_escort_timing(update, context)
    
    # Se stiamo aspettando km
    elif context.user_data.get('waiting_for_km'):
        return await handle_mission_km(update, context)
    
    # Default: non dovremmo arrivare qui
    await update.message.reply_text(
        "❌ Errore: stato non riconosciuto. Usa /start per ricominciare.",
        parse_mode='HTML'
    )
    return ConversationHandler.END


async def handle_meal_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle meal checkbox selection"""
    query = update.callback_query
    await query.answer()
    
    meal_type = query.data.replace("meal_", "")
    
    # Toggle meal selection
    if 'selected_meals' not in context.user_data:
        context.user_data['selected_meals'] = set()
    
    if meal_type in context.user_data['selected_meals']:
        context.user_data['selected_meals'].remove(meal_type)
    else:
        context.user_data['selected_meals'].add(meal_type)
    
    # Calculate meal reimbursement
    meals_not_consumed = len(context.user_data['selected_meals'])
    meal_reimbursement = 0
    
    if meals_not_consumed == 1:
        meal_reimbursement = MEAL_RATES['single_meal_net']
    elif meals_not_consumed == 2:
        meal_reimbursement = MEAL_RATES['double_meal_net']
    
    context.user_data['meal_reimbursement'] = meal_reimbursement
    context.user_data['meals_not_consumed'] = meals_not_consumed
    
    # Update message
    text = "🍽️ <b>PASTI NON CONSUMATI</b>\n\n"
    text += "Seleziona i pasti che NON hai consumato:\n\n"
    
    lunch_check = "☑️" if "lunch" in context.user_data['selected_meals'] else "☐"
    dinner_check = "☑️" if "dinner" in context.user_data['selected_meals'] else "☐"
    
    text += f"{lunch_check} Pranzo\n"
    text += f"{dinner_check} Cena\n\n"
    
    if meal_reimbursement > 0:
        text += f"💰 Rimborso pasti: {format_currency(meal_reimbursement)}\n\n"
    
    keyboard = [
        [
            InlineKeyboardButton(f"{lunch_check} Pranzo", callback_data="meal_lunch"),
            InlineKeyboardButton(f"{dinner_check} Cena", callback_data="meal_dinner")
        ],
        [InlineKeyboardButton("✅ Conferma", callback_data="meal_confirm")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Create conversation handler



async def handle_second_day_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle second day payment type"""
    query = update.callback_query
    await query.answer()
    
    second_day_type = "FORFEIT" if "forfeit" in query.data else "ORDINARY"
    context.user_data['second_day_type'] = second_day_type
    
    # Procedi al riepilogo finale
    return await show_service_summary(update, context)

async def handle_forfeit_continuation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle forfeit continuation choice"""
    query = update.callback_query
    await query.answer()
    
    continues = query.data == "forfeit_continues_yes"
    context.user_data['forfeit_continues'] = continues
    
    if continues:
        # Chiedi dettagli del giorno successivo
        text = "📅 <b>SERVIZIO GIORNO SUCCESSIVO</b>\n\n"
        text += "A che ora termina il servizio domani?\n"
        text += "(Inserisci orario in formato HH:MM)"
        
        await query.edit_message_text(text, parse_mode='HTML')
        context.user_data['waiting_for_next_day_end'] = True
        
        return CONFIRM_SERVICE
    else:
        # Procedi al riepilogo
        return await show_service_summary(update, context)

async def handle_next_day_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle next day end time input"""
    if not context.user_data.get('waiting_for_next_day_end'):
        return
    
    text = update.message.text.strip()
    hour, minute = validate_time_input(text)
    
    if hour is None:
        await update.message.reply_text(
            "❌ Formato non valido! Usa HH:MM (es: 20:00)",
            parse_mode='HTML'
        )
        return CONFIRM_SERVICE
    
    # Calcola orario fine del giorno successivo
    service_date = context.user_data['service_date']
    next_day = service_date + timedelta(days=1)
    next_day_end = datetime.combine(next_day, time(hour, minute))
    
    # Aggiorna orario fine e ore totali
    context.user_data['original_end_time'] = context.user_data['end_time']
    context.user_data['end_time'] = next_day_end
    
    # Ricalcola ore totali
    start_time = context.user_data['start_time']
    total_hours = (next_day_end - start_time).total_seconds() / 3600
    context.user_data['total_hours'] = total_hours
    context.user_data['forfeit_days'] = 2  # Servizio su 2 giorni
    
    context.user_data['waiting_for_next_day_end'] = False
    
    # Mostra riepilogo
    text = f"✅ <b>SERVIZIO FORFETTARIO 2 GIORNI</b>\n\n"
    text += f"Inizio: {start_time.strftime('%d/%m %H:%M')}\n"
    text += f"Fine: {next_day_end.strftime('%d/%m %H:%M')}\n"
    text += f"Totale: {total_hours:.0f} ore\n\n"
    
    # Calcola forfettario
    if total_hours >= 24:
        forfeit_amount = 110.00  # Prime 24h
        if total_hours >= 36:  # Più di 1.5 giorni
            forfeit_amount += 110.00  # Altre 24h
        elif total_hours > 24:  # Tra 24 e 36 ore
            forfeit_amount += 50.00  # 12-24h extra
    else:
        forfeit_amount = 50.00 if total_hours >= 12 else 0
    
    text += f"💰 Forfettario: € {forfeit_amount:.2f} netti\n\n"
    
    context.user_data['forfeit_amount'] = forfeit_amount
    
    # Chiedi se procede con altro forfettario o termina
    text += "Il secondo giorno è ancora forfettario?"
    
    keyboard = [
        [
            InlineKeyboardButton("💰 Sì, forfettario", callback_data="second_day_forfeit"),
            InlineKeyboardButton("📋 No, ordinario", callback_data="second_day_ordinary")
        ]
    ]
    
    await update.message.reply_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return CONFIRM_SERVICE


service_conversation_handler = ConversationHandler( entry_points=[
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
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_destination)
        ],
        TRAVEL_DETAILS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_travel_sheet_number)
        ],
        TRAVEL_TYPE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_travel_type_input)
        ],
        MEAL_DETAILS: [
            CallbackQueryHandler(handle_mission_type, pattern="^mission_type_")
        ],
        CONFIRM_SERVICE: [
            CallbackQueryHandler(handle_meals, pattern="^meals_"),
            CallbackQueryHandler(handle_confirmation, pattern="^confirm_")
        ]
    },
    fallbacks=[CommandHandler("start", start_command),
            CallbackQueryHandler(handle_forfeit_continuation, pattern="^forfeit_continues_"),
            CallbackQueryHandler(handle_second_day_type, pattern="^second_day_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_next_day_end_time)],
    )

# ------------------------------
# Stub autocreato: mancante `service_conversation_handler`
# ------------------------------
