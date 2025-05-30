"""
Overtime management handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, date
from sqlalchemy import extract, func

from database.connection import SessionLocal
from database.models import User, Overtime, OvertimeType

from utils.clean_chat import register_bot_message, delete_message_after_delay
from config.settings import get_current_date
from config.constants import OVERTIME_RATES
from utils.formatters import format_currency, format_hours, format_month_year
from utils.keyboards import get_month_keyboard, get_back_keyboard

async def overtime_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show overtime management dashboard"""
    user_id = str(update.effective_user.id)
    current_date = get_current_date()
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get current month overtime
        current_month_ot = db.query(Overtime).filter(
            Overtime.user_id == user.id,
            extract('month', Overtime.date) == current_date.month,
            extract('year', Overtime.date) == current_date.year
        ).all()
        
        # Group by type and payment status
        by_type = {}
        paid_hours = 0
        paid_amount = 0
        unpaid_hours = 0
        unpaid_amount = 0
        
        for ot in current_month_ot:
            type_key = ot.overtime_type.value
            if type_key not in by_type:
                by_type[type_key] = {'hours': 0, 'amount': 0}
            
            by_type[type_key]['hours'] += ot.hours
            by_type[type_key]['amount'] += ot.amount
            
            if ot.is_paid:
                paid_hours += ot.hours
                paid_amount += ot.amount
            else:
                unpaid_hours += ot.hours
                unpaid_amount += ot.amount
        
        # Get total accumulated overtime
        total_unpaid = db.query(
            func.sum(Overtime.hours),
            func.sum(Overtime.amount)
        ).filter(
            Overtime.user_id == user.id,
            Overtime.is_paid == False
        ).first()
        
        total_unpaid_hours = total_unpaid[0] or 0
        total_unpaid_amount = total_unpaid[1] or 0
        
        # Format message
        text = f"⏰ <b>GESTIONE STRAORDINARI {format_month_year(current_date)}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📊 <b>RIEPILOGO PER TIPOLOGIA:</b>\n"
        
        type_names = {
            'WEEKDAY_DAY': 'Feriale Diurno',
            'WEEKDAY_NIGHT': 'Feriale Notturno',
            'HOLIDAY_DAY': 'Festivo Diurno',
            'HOLIDAY_NIGHT': 'Festivo Notturno'
        }
        
        for type_key, data in by_type.items():
            rate = OVERTIME_RATES[type_key.lower()]
            text += f"├ {type_names[type_key]}: {data['hours']:.1f}h × "
            text += f"{format_currency(rate)} = {format_currency(data['amount'])}\n"
        
        total_hours = paid_hours + unpaid_hours
        total_amount = paid_amount + unpaid_amount
        text += f"└ TOTALE: {total_hours:.0f}h = {format_currency(total_amount)}\n\n"
        
        text += "💰 <b>SITUAZIONE PAGAMENTI:</b>\n"
        text += f"├ Ore pagate questo mese: {paid_hours:.0f}h\n"
        text += f"├ Importo pagato: {format_currency(paid_amount)}\n"
        text += f"├ Ore NON pagate: {unpaid_hours:.0f}h\n"
        text += f"├ Importo da ricevere: {format_currency(unpaid_amount)}\n"
        
        if unpaid_hours >= 55:
            text += "└ ⚠️ Limite mensile raggiunto!\n"
        else:
            text += f"└ Ore rimanenti pagabili: {55 - paid_hours:.0f}h\n"
        
        text += f"\n📈 <b>STRAORDINARI ACCUMULATI {current_date.year}:</b>\n"
        text += f"├ Totale ore accumulate: {total_unpaid_hours:.0f}h\n"
        text += f"├ Valore totale: {format_currency(total_unpaid_amount)}\n"
        text += "└ Prossimo pagamento: GIUGNO/DICEMBRE\n"
        
        # Keyboard
        keyboard = [
            [
                InlineKeyboardButton("📊 Dettaglio ore", callback_data="overtime_detail"),
                InlineKeyboardButton("💰 Simula pagamento", callback_data="overtime_simulate")
            ],
            [
                InlineKeyboardButton("📝 Inserisci ore pagate", callback_data="overtime_paid"),
                InlineKeyboardButton("📈 Storico", callback_data="overtime_history")
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
            
    finally:
        db.close()

async def overtime_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle overtime callbacks"""
    query = update.callback_query
    action = query.data.replace("overtime_", "")
    
    if action == "detail":
        await show_overtime_detail(update, context)
    elif action == "simulate":
        await simulate_payment(update, context)
    elif action == "paid":
        await ask_paid_hours(update, context)
    elif action == "history":
        await show_overtime_history(update, context)

async def show_overtime_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed overtime breakdown by month"""
    user_id = str(update.effective_user.id)
    current_year = datetime.now().year
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get overtime grouped by month
        monthly_data = db.query(
            extract('month', Overtime.date).label('month'),
            func.sum(Overtime.hours).label('total_hours'),
            func.sum(Overtime.amount).label('total_amount'),
            func.sum(func.case([(Overtime.is_paid == True, Overtime.hours)], else_=0)).label('paid_hours'),
            func.sum(func.case([(Overtime.is_paid == False, Overtime.hours)], else_=0)).label('unpaid_hours')
        ).filter(
            Overtime.user_id == user.id,
            extract('year', Overtime.date) == current_year
        ).group_by(
            extract('month', Overtime.date)
        ).all()
        
        text = f"📊 <b>DETTAGLIO STRAORDINARI {current_year}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        months = {
            1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
            5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
            9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
        }
        
        total_accumulated = 0
        
        for data in monthly_data:
            month_name = months[data.month]
            text += f"<b>{month_name}:</b>\n"
            text += f"├ Ore totali: {data.total_hours:.0f}h\n"
            text += f"├ Ore pagate: {data.paid_hours:.0f}h\n"
            text += f"├ Ore accumulate: {data.unpaid_hours:.0f}h\n"
            text += f"└ Valore totale: {format_currency(data.total_amount)}\n\n"
            
            total_accumulated += data.unpaid_hours
        
        text += f"<b>TOTALE ORE ACCUMULATE: {total_accumulated:.0f}h</b>"
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Indietro", callback_data="back_overtime")]
            ])
        )
        
    finally:
        db.close()

async def simulate_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simulate accumulated overtime payment"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get all unpaid overtime
        unpaid = db.query(Overtime).filter(
            Overtime.user_id == user.id,
            Overtime.is_paid == False
        ).all()
        
        # Group by type
        by_type = {}
        for ot in unpaid:
            type_key = ot.overtime_type.value
            if type_key not in by_type:
                by_type[type_key] = {'hours': 0, 'amount': 0}
            
            by_type[type_key]['hours'] += ot.hours
            by_type[type_key]['amount'] += ot.amount
        
        total_hours = sum(data['hours'] for data in by_type.values())
        gross_amount = sum(data['amount'] for data in by_type.values())
        
        # Apply IRPEF
        net_amount = gross_amount * (1 - user.irpef_rate)
        
        text = "💰 <b>SIMULAZIONE PAGAMENTO ECCEDENZE</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += f"📅 Prossimo pagamento: GIUGNO {datetime.now().year}\n\n"
        
        text += "<b>DETTAGLIO ORE ACCUMULATE:</b>\n"
        
        type_names = {
            'WEEKDAY_DAY': 'Feriale Diurno',
            'WEEKDAY_NIGHT': 'Feriale Notturno',
            'HOLIDAY_DAY': 'Festivo Diurno',
            'HOLIDAY_NIGHT': 'Festivo Notturno'
        }
        
        for type_key, data in by_type.items():
            text += f"├ {type_names[type_key]}: {data['hours']:.1f}h = "
            text += f"{format_currency(data['amount'])}\n"
        
        text += f"\n<b>CALCOLO IMPORTI:</b>\n"
        text += f"├ Ore totali: {total_hours:.0f}h\n"
        text += f"├ Importo lordo: {format_currency(gross_amount)}\n"
        text += f"├ IRPEF ({int(user.irpef_rate * 100)}%): -{format_currency(gross_amount * user.irpef_rate)}\n"
        text += f"└ <b>NETTO IN TASCA: {format_currency(net_amount)}</b>\n"
        
        text += "\n💡 <i>Questo importo sarà pagato automaticamente "
        text += "a giugno e dicembre di ogni anno</i>"
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Indietro", callback_data="back_overtime")]
            ])
        )
        
    finally:
        db.close()

async def paid_hours_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for paid hours input"""
    await ask_paid_hours(update, context)

async def ask_paid_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask user to input paid hours for the month"""
    current_date = get_current_date()
    
    text = "💰 <b>AGGIORNAMENTO PAGAMENTO STRAORDINARI</b>\n\n"
    text += f"Mese: <b>{format_month_year(current_date)}</b>\n\n"
    text += "Quante ore di straordinario ti sono state pagate questo mese?\n\n"
    text += "⚠️ Max pagabile: 55 ore\n\n"
    text += "Inserisci il numero di ore:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode='HTML')
    else:
        await update.message.reply_text(text, parse_mode='HTML')
    
    # Set conversation state
    context.user_data['waiting_for_paid_hours'] = True

async def accumulation_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show accumulated overtime"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get all unpaid overtime grouped by year
        yearly_data = db.query(
            extract('year', Overtime.date).label('year'),
            func.sum(Overtime.hours).label('hours'),
            func.sum(Overtime.amount).label('amount')
        ).filter(
            Overtime.user_id == user.id,
            Overtime.is_paid == False
        ).group_by(
            extract('year', Overtime.date)
        ).all()
        
        text = "📈 <b>STRAORDINARI ACCUMULATI</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        total_hours = 0
        total_amount = 0
        
        for data in yearly_data:
            text += f"<b>Anno {int(data.year)}:</b>\n"
            text += f"├ Ore accumulate: {data.hours:.0f}h\n"
            text += f"├ Valore: {format_currency(data.amount)}\n"
            text += f"└ Pagamento: Giugno/Dicembre {int(data.year)}\n\n"
            
            total_hours += data.hours
            total_amount += data.amount
        
        text += f"<b>TOTALE GENERALE:</b>\n"
        text += f"├ Ore: {total_hours:.0f}h\n"
        text += f"└ Valore: {format_currency(total_amount)}\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
    finally:
        db.close()

async def show_overtime_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show overtime payment history"""
    # TODO: Implement payment history when payment recording is added
    text = "📈 <b>STORICO PAGAMENTI STRAORDINARI</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "⚠️ Funzionalità in sviluppo\n\n"
    text += "Qui vedrai lo storico dei pagamenti delle eccedenze"
    
    await update.callback_query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Indietro", callback_data="back_overtime")]
        ])
    )