"""
Leave management handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, date, timedelta
from sqlalchemy import extract, func, and_

from database.connection import SessionLocal, get_db
from database.models import User, Leave, LeaveType

from utils.clean_chat import register_bot_message, delete_message_after_delay
from config.settings import get_current_date, LEAVE_DATES, LEAVE_TYPE
from utils.formatters import format_date, format_days
from utils.keyboards import get_leave_type_keyboard, get_back_keyboard

async def leave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leave management dashboard"""
    user_id = str(update.effective_user.id)
    current_date = get_current_date()
    current_year = current_date.year
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Calculate remaining leaves
        remaining_current = user.current_year_leave - user.current_year_leave_used
        
        # Get leave usage for current year
        year_leaves = db.query(Leave).filter(
            Leave.user_id == user.id,
            extract('year', Leave.start_date) == current_year,
            Leave.leave_type == LeaveType.ORDINARY_CURRENT,
            Leave.is_cancelled == False
        ).all()
        
        # Calculate previous year deadline
        previous_deadline = date(current_year, 3, 31)
        days_to_deadline = (previous_deadline - current_date).days
        
        text = "🏖️ <b>GESTIONE LICENZE E PERMESSI</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📅 <b>SITUAZIONE ATTUALE:</b>\n\n"
        
        text += f"<b>LICENZA ORDINARIA {current_year}:</b>\n"
        text += f"├ Spettanti: {user.current_year_leave} giorni\n"
        text += f"├ Utilizzati: {user.current_year_leave_used} giorni\n"
        text += f"├ <b>RESIDUI: {remaining_current} giorni</b>\n"
        text += f"└ Scadenza: 31/12/{current_year + 1}\n\n"
        
        text += f"<b>LICENZA ORDINARIA {current_year - 1}:</b>\n"
        text += f"├ Riportati: {user.previous_year_leave} giorni\n"
        text += f"├ Utilizzati: 0 giorni\n"  # TODO: Track previous year usage
        text += f"├ <b>RESIDUI: {user.previous_year_leave} giorni</b>\n"
        
        if days_to_deadline > 0:
            text += f"└ ⚠️ <b>SCADENZA: 31/03/{current_year} ({days_to_deadline} giorni)</b>\n\n"
        else:
            text += f"└ ❌ <b>SCADUTE IL 31/03/{current_year}</b>\n\n"
        
        # Other permits
        text += "<b>ALTRI PERMESSI:</b>\n"
        text += "├ Donazione sangue: 2/4 disponibili\n"
        text += "├ L.104: 3gg/mese\n"
        text += "├ Congedo matrimoniale: 15gg (non usato)\n"
        text += "└ Studio: 150h/anno (120h residue)\n\n"
        
        # Usage chart
        if year_leaves:
            text += f"📊 <b>UTILIZZO LICENZE {current_year}:</b>\n"
            
            months_used = {}
            for leave in year_leaves:
                month = leave.start_date.month
                if month not in months_used:
                    months_used[month] = 0
                months_used[month] += leave.days
            
            months = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", 
                     "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
            
            for i, month_name in enumerate(months):
                if i + 1 in months_used:
                    days = months_used[i + 1]
                    text += f"{month_name}: {'■' * days} ({days}gg)\n"
        
        # Warnings
        if user.previous_year_leave > 0 and days_to_deadline > 0 and days_to_deadline <= 60:
            text += f"\n⚠️ <b>AVVISI:</b>\n"
            text += f"├ {user.previous_year_leave}gg licenza {current_year - 1} scadono il 31/03!\n"
            text += f"├ Pianifica utilizzo entro {days_to_deadline} giorni\n"
            text += "└ Usa il pulsante 'Pianifica licenze'\n"
        
        # Keyboard
        keyboard = [
            [
                InlineKeyboardButton("➕ Inserisci licenza", callback_data="leave_add"),
                InlineKeyboardButton("📅 Pianifica licenze", callback_data="leave_plan")
            ],
            [
                InlineKeyboardButton("📊 Report annuale", callback_data="leave_report"),
                InlineKeyboardButton("⚙️ Configura permessi", callback_data="leave_config")
            ],
            [InlineKeyboardButton("⬅️ Menu principale", callback_data="back_to_menu")]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        db.close()

    finally:
        db.close()
async def leave_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leave callbacks"""
    query = update.callback_query
    action = query.data.replace("leave_", "")
    
    if action == "add":
        await start_leave_registration(update, context)
    elif action == "plan":
        await show_leave_planner(update, context)
    elif action == "report":
        await show_leave_report(update, context)
    elif action == "config":
        await show_leave_config(update, context)
    elif action.startswith("type_"):
        await handle_leave_type(update, context)
    elif action == "confirm":
        await confirm_leave(update, context)

async def add_leave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add new leave"""
    await start_leave_registration(update, context)

async def start_leave_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start leave registration process"""
    text = "➕ <b>INSERIMENTO LICENZA</b>\n\n"
    text += "Tipo di assenza:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=get_leave_type_keyboard()
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode='HTML',
            reply_markup=get_leave_type_keyboard()
        )
    
    return LEAVE_TYPE

async def handle_leave_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leave type selection"""
    query = update.callback_query
    await query.answer()
    
    leave_type = query.data.replace("leave_type_", "")
    context.user_data['leave_type'] = leave_type
    
    # Get user to check availability
    user_id = str(query.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Check availability
        available = 0
        type_name = ""
        
        if leave_type == "current":
            available = user.current_year_leave - user.current_year_leave_used
            type_name = f"Licenza ordinaria {datetime.now().year}"
        elif leave_type == "previous":
            available = user.previous_year_leave
            type_name = f"Licenza ordinaria {datetime.now().year - 1}"
        elif leave_type == "blood":
            available = 4 - 2  # TODO: Track blood donations
            type_name = "Donazione sangue"
        elif leave_type == "104":
            available = 3  # Monthly
            type_name = "L.104"
        elif leave_type == "study":
            available = 150 - 30  # TODO: Track study hours
            type_name = "Permesso studio"
        elif leave_type == "marriage":
            available = 15
            type_name = "Congedo matrimoniale"
        else:
            available = 999  # Other types
            type_name = "Altro permesso"
        
        context.user_data['available_days'] = available
        context.user_data['leave_type_name'] = type_name
        
        if available <= 0:
            await query.edit_message_text(
                f"❌ Non hai giorni disponibili per: {type_name}",
                parse_mode='HTML',
                reply_markup=get_back_keyboard("back_to_leave")
            )
            return
        
        text = f"📅 <b>{type_name.upper()}</b>\n\n"
        text += f"Giorni disponibili: <b>{available}</b>\n\n"
        text += "Inserisci la data di inizio (GG/MM/AAAA):"
        
        await query.edit_message_text(text, parse_mode='HTML')
        
        db.close()
    
    finally:
        db.close()
    return LEAVE_DATES

async def handle_leave_dates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leave date input"""
    text = update.message.text
    
    # Parse date
    try:
        if 'start_date' not in context.user_data:
            # Parse start date
            parts = text.split('/')
            start_date = date(int(parts[2]), int(parts[1]), int(parts[0]))
            context.user_data['start_date'] = start_date
            
            await update.message.reply_text(
                "Inserisci la data di fine (GG/MM/AAAA):",
                parse_mode='HTML'
            )
            return LEAVE_DATES
        else:
            # Parse end date
            parts = text.split('/')
            end_date = date(int(parts[2]), int(parts[1]), int(parts[0]))
            
            start_date = context.user_data['start_date']
            
            # Validate dates
            if end_date < start_date:
                await update.message.reply_text(
                    "❌ La data di fine non può essere prima della data di inizio!",
                    parse_mode='HTML'
                )
                return LEAVE_DATES
            
            # Calculate days
            days = (end_date - start_date).days + 1
            available = context.user_data['available_days']
            
            if days > available:
                await update.message.reply_text(
                    f"❌ Hai richiesto {days} giorni ma ne hai solo {available} disponibili!",
                    parse_mode='HTML'
                )
                return LEAVE_DATES
            
            context.user_data['end_date'] = end_date
            context.user_data['days'] = days
            
            # Show summary
            await show_leave_summary(update, context)
            
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Formato data non valido! Usa GG/MM/AAAA",
            parse_mode='HTML'
        )
        return LEAVE_DATES

async def show_leave_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leave summary for confirmation"""
    start_date = context.user_data['start_date']
    end_date = context.user_data['end_date']
    days = context.user_data['days']
    leave_type_name = context.user_data['leave_type_name']
    available = context.user_data['available_days']
    
    text = "✅ <b>RIEPILOGO LICENZA</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"Tipo: <b>{leave_type_name}</b>\n"
    text += f"Dal: <b>{format_date(start_date)}</b>\n"
    text += f"Al: <b>{format_date(end_date)}</b>\n\n"
    text += f"✅ Totale: <b>{days} giorni</b>\n"
    text += f"├ Disponibili prima: {available}gg\n"
    text += f"├ Utilizzati: {days}gg\n"
    text += f"└ Residui dopo: {available - days}gg\n"
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Conferma", callback_data="leave_confirm"),
            InlineKeyboardButton("❌ Annulla", callback_data="back_to_leave")
        ]
    ]
    
    await update.message.reply_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and save leave"""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Create leave record
        leave_type_map = {
            'current': LeaveType.ORDINARY_CURRENT,
            'previous': LeaveType.ORDINARY_PREVIOUS,
            'sick': LeaveType.SICK,
            'blood': LeaveType.BLOOD_DONATION,
            '104': LeaveType.LAW_104,
            'study': LeaveType.STUDY,
            'marriage': LeaveType.MARRIAGE,
            'other': LeaveType.OTHER
        }
        
        leave_type = leave_type_map.get(context.user_data['leave_type'], LeaveType.OTHER)
        
        leave = Leave(
            user_id=user.id,
            leave_type=leave_type,
            start_date=context.user_data['start_date'],
            end_date=context.user_data['end_date'],
            days=context.user_data['days']
        )
        
        db.add(leave)
        
        # Update user leave balance
        if leave_type == LeaveType.ORDINARY_CURRENT:
            user.current_year_leave_used += leave.days
        elif leave_type == LeaveType.ORDINARY_PREVIOUS:
            # TODO: Track previous year usage separately
            pass
        
        db.commit()
        
        text = "✅ <b>Licenza registrata con successo!</b>\n\n"
        text += f"Periodo: {format_date(leave.start_date)} - {format_date(leave.end_date)}\n"
        text += f"Giorni: {leave.days}\n\n"
        text += "📅 La licenza è stata aggiunta al calendario."
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏖️ Gestione licenze", callback_data="back_to_leave")]
            ])
        )
        
        # Clear context
        context.user_data.clear()
        
        db.close()

    finally:
        db.close()
async def plan_leave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leave planner"""
    await show_leave_planner(update, context)

async def show_leave_planner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leave planning assistant"""
    user_id = str(update.effective_user.id)
    current_date = get_current_date()
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        text = "📅 <b>PIANIFICATORE LICENZE INTELLIGENTE</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Check expiring leaves
        if user.previous_year_leave > 0:
            deadline = date(current_date.year, 3, 31)
            days_left = (deadline - current_date).days
            
            if days_left > 0:
                text += f"⚠️ <b>LICENZE IN SCADENZA:</b>\n"
                text += f"Hai {user.previous_year_leave} giorni del {current_date.year - 1} "
                text += f"che scadono tra {days_left} giorni!\n\n"
                
                # Suggest dates
                text += "📌 <b>DATE SUGGERITE:</b>\n"
                
                # Find best periods (avoiding weekends)
                suggestion_date = current_date + timedelta(days=7)
                suggestions = []
                
                while len(suggestions) < 3 and suggestion_date < deadline:
                    if suggestion_date.weekday() < 5:  # Not weekend
                        # Check if already on leave
                        existing = db.query(Leave).filter(
                            Leave.user_id == user.id,
                            Leave.start_date <= suggestion_date,
                            Leave.end_date >= suggestion_date,
                            Leave.is_cancelled == False
                        ).first()
                        
                        if not existing:
                            suggestions.append(suggestion_date)
                    
                    suggestion_date += timedelta(days=1)
                
                for i, date_sug in enumerate(suggestions):
                    text += f"{i+1}. {format_date(date_sug)} ({date_sug.strftime('%A')})\n"
        
        # Current year planning
        remaining = user.current_year_leave - user.current_year_leave_used
        text += f"\n📊 <b>LICENZE {current_date.year}:</b>\n"
        text += f"Hai ancora {remaining} giorni da pianificare.\n\n"
        
        # Optimal distribution
        text += "💡 <b>DISTRIBUZIONE OTTIMALE:</b>\n"
        months_left = 12 - current_date.month + 1
        if months_left > 0:
            per_month = remaining / months_left
            text += f"├ {per_month:.1f} giorni/mese\n"
            text += f"├ 1 settimana ogni {int(52/remaining*7)} giorni\n"
            text += f"└ Prossima licenza suggerita: tra {int(30/per_month)} giorni\n"
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Pianifica ora", callback_data="leave_add")],
                [InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_leave")]
            ])
        )
        
        db.close()

    finally:
        db.close()
async def show_leave_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show annual leave report"""
    user_id = str(update.effective_user.id)
    current_year = datetime.now().year
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get all leaves for current year
        leaves = db.query(Leave).filter(
            Leave.user_id == user.id,
            extract('year', Leave.start_date) == current_year,
            Leave.is_cancelled == False
        ).order_by(Leave.start_date).all()
        
        text = f"📊 <b>REPORT LICENZE {current_year}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Summary by type
        by_type = {}
        total_days = 0
        
        for leave in leaves:
            type_key = leave.leave_type.value
            if type_key not in by_type:
                by_type[type_key] = {'count': 0, 'days': 0}
            
            by_type[type_key]['count'] += 1
            by_type[type_key]['days'] += leave.days
            total_days += leave.days
        
        text += "📋 <b>RIEPILOGO PER TIPOLOGIA:</b>\n"
        
        type_names = {
            'ORDINARY_CURRENT': f'Licenza ordinaria {current_year}',
            'ORDINARY_PREVIOUS': f'Licenza ordinaria {current_year - 1}',
            'SICK': 'Malattia',
            'BLOOD_DONATION': 'Donazione sangue',
            'LAW_104': 'L.104',
            'STUDY': 'Permesso studio',
            'MARRIAGE': 'Congedo matrimoniale',
            'OTHER': 'Altri permessi'
        }
        
        for type_key, data in by_type.items():
            name = type_names.get(type_key, type_key)
            text += f"├ {name}: {data['days']}gg ({data['count']} volte)\n"
        
        text += f"└ <b>TOTALE: {total_days} giorni</b>\n\n"
        
        # Detailed list
        if leaves:
            text += "📅 <b>DETTAGLIO LICENZE:</b>\n"
            for leave in leaves[-10:]:  # Last 10
                text += f"├ {format_date(leave.start_date)} - {format_date(leave.end_date)} "
                text += f"({leave.days}gg) - {type_names.get(leave.leave_type.value, 'Altro')}\n"
            
            if len(leaves) > 10:
                text += f"└ ...e altre {len(leaves) - 10} licenze\n"
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_leave")]
            ])
        )
        
        db.close()

    finally:
        db.close()
async def show_leave_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leave configuration"""
    # TODO: Implement leave configuration
    text = "⚙️ <b>CONFIGURAZIONE PERMESSI</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "⚠️ Funzionalità in sviluppo\n\n"
    text += "Qui potrai configurare:\n"
    text += "- Giorni di licenza annuali\n"
    text += "- Permessi speciali disponibili\n"
    text += "- Alert e notifiche\n"
    
    await update.callback_query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_leave")]
        ])
    )


async def handle_leave_value_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leave value input for editing"""
    if not context.user_data.get('waiting_for_leave_value'):
        return
    
    try:
        value = int(update.message.text.strip())
        if value < 0 or value > 50:
            await update.message.reply_text("❌ Inserisci un valore tra 0 e 50")
            return
        
        user_id = str(update.effective_user.id)
        editing_type = context.user_data.get('editing_leave')
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if 'current_leave_total' in editing_type:
                user.current_year_leave = value
                field = "Licenza totale anno corrente"
            elif 'current_leave_used' in editing_type:
                user.current_year_leave_used = value
                field = "Licenza utilizzata"
            elif 'previous_leave' in editing_type:
                user.previous_year_leave = value
                field = "Licenza residua anno precedente"
            
            db.commit()
            
            await update.message.reply_text(
                f"✅ {field} aggiornata: {value} giorni",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏖️ Torna alle licenze", callback_data="settings_leaves")]
                ])
            )
            
            db.close()
            context.user_data['waiting_for_leave_value'] = False
            context.user_data['editing_leave'] = None
            
        except ValueError:
            await update.message.reply_text("❌ Inserisci un numero valido!")

    finally:
        db.close()
async def handle_route_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle route name input"""
    if not context.user_data.get('adding_route'):
        return
    
    route_name = update.message.text.strip()
    context.user_data['route_name'] = route_name
    context.user_data['adding_route'] = False
    context.user_data['adding_route_km'] = True
    
    await update.message.reply_text(
        f"📏 Quanti km è il percorso '{route_name}'?",
        parse_mode='HTML'
    )

async def handle_route_km_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle route km input"""
    if not context.user_data.get('adding_route_km'):
        return
    
    try:
        km = int(update.message.text.strip())
        if km <= 0:
            await update.message.reply_text("❌ I km devono essere maggiori di 0!")
            return
        
        user_id = str(update.effective_user.id)
        route_name = context.user_data.get('route_name')
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            if not user.saved_routes:
                user.saved_routes = {}
            
            user.saved_routes[route_name] = {'km': km}
            db.commit()
            
            await update.message.reply_text(
                f"✅ Percorso salvato!\n\n"
                f"📍 {route_name}: {km} km",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📍 Torna ai percorsi", callback_data="settings_location")]
                ])
            )
            
            context.user_data['adding_route_km'] = False
            context.user_data['route_name'] = None
            
        finally:
            db.close()
            
    except ValueError:
        await update.message.reply_text("❌ Inserisci un numero valido!")

async def handle_patron_saint_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle patron saint date input"""
    if not context.user_data.get('setting_patron_saint'):
        return
    
    text = update.message.text.strip()
    
    try:
        parts = text.split('/')
        if len(parts) == 2:
            day, month = int(parts[0]), int(parts[1])
            # Usa anno corrente per validazione
            patron_date = date(datetime.now().year, month, day)
            
            user_id = str(update.effective_user.id)
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                user.patron_saint_date = patron_date
                db.commit()
                
                await update.message.reply_text(
                    f"✅ Santo Patrono impostato: {day:02d}/{month:02d}",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📍 Torna alle impostazioni", callback_data="settings_location")]
                    ])
                )
                
                context.user_data['setting_patron_saint'] = False
                
            finally:
                db.close()
                
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Formato non valido! Usa GG/MM (es: 29/09)"
        )

async def handle_reminder_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reminder time input"""
    if not context.user_data.get('setting_reminder_time'):
        return
    
    text = update.message.text.strip()
    
    try:
        parts = text.split(':')
        if len(parts) == 2:
            hour, minute = int(parts[0]), int(parts[1])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                time_str = f"{hour:02d}:{minute:02d}"
                
                user_id = str(update.effective_user.id)
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.telegram_id == user_id).first()
                    
                    if not user.notification_settings:
                        user.notification_settings = {}
                    
                    user.notification_settings['reminder_time'] = time_str
                    db.commit()
                    
                    await update.message.reply_text(
                        f"✅ Orario notifiche impostato: {time_str}",
                        parse_mode='HTML',
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔔 Torna alle notifiche", callback_data="settings_notifications")]
                        ])
                    )
                    
                    context.user_data['setting_reminder_time'] = False
                    
                finally:
                    db.close()
            else:
                raise ValueError("Orario non valido")
                
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Formato non valido! Usa HH:MM (es: 09:00)"
        )


