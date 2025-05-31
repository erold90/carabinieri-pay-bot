"""
Rest and recovery management handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, date, timedelta
from sqlalchemy import extract, func, and_, or_

from database.connection import SessionLocal, get_db
from database.models import User, Service, Rest, RestType
from config.settings import get_current_date
from utils.formatters import format_date, format_currency
from utils.keyboards import get_back_keyboard

async def rest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show rest management dashboard"""
    user_id = str(update.effective_user.id)
    current_date = get_current_date()
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Statistiche riposi
        current_month = current_date.month
        current_year = current_date.year
        
        # Riposi pianificati questo mese
        monthly_rests = db.query(Rest).filter(
            Rest.user_id == user.id,
            extract('month', Rest.scheduled_date) == current_month,
            extract('year', Rest.scheduled_date) == current_year
        ).all()
        
        # Riposi da recuperare
        pending_recoveries = db.query(Rest).filter(
            Rest.user_id == user.id,
            Rest.is_worked == True,
            Rest.is_recovered == False,
            Rest.recovery_due_date >= current_date
        ).order_by(Rest.recovery_due_date).all()
        
        # Riposi scaduti (non recuperati entro 4 settimane)
        expired_recoveries = db.query(Rest).filter(
            Rest.user_id == user.id,
            Rest.is_worked == True,
            Rest.is_recovered == False,
            Rest.recovery_due_date < current_date
        ).all()
        
        text = "🛌 <b>GESTIONE RIPOSI E RECUPERI</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Riepilogo mensile
        text += f"📅 <b>SITUAZIONE {current_date.strftime('%B %Y').upper()}:</b>\n\n"
        
        weekly_count = sum(1 for r in monthly_rests if r.rest_type == RestType.WEEKLY)
        holiday_count = sum(1 for r in monthly_rests if r.rest_type == RestType.HOLIDAY)
        worked_count = sum(1 for r in monthly_rests if r.is_worked)
        
        text += f"Riposi settimanali pianificati: {weekly_count}\n"
        text += f"├ Fruiti regolarmente: {weekly_count - sum(1 for r in monthly_rests if r.rest_type == RestType.WEEKLY and r.is_worked)}\n"
        text += f"└ Lavorati (da recuperare): {sum(1 for r in monthly_rests if r.rest_type == RestType.WEEKLY and r.is_worked)}\n\n"
        
        text += f"Festività infrasettimanali: {holiday_count}\n"
        text += f"├ Riposate: {holiday_count - sum(1 for r in monthly_rests if r.rest_type == RestType.HOLIDAY and r.is_worked)}\n"
        text += f"└ Lavorate: {sum(1 for r in monthly_rests if r.rest_type == RestType.HOLIDAY and r.is_worked)}\n\n"
        
        # Alert recuperi
        if pending_recoveries:
            text += "⚠️ <b>RECUPERI DA EFFETTUARE:</b>\n"
            for rest in pending_recoveries[:3]:
                days_left = (rest.recovery_due_date - current_date).days
                emoji = "🔴" if days_left <= 7 else "🟡"
                text += f"{emoji} {format_date(rest.scheduled_date)} - "
                text += f"Scade tra {days_left} giorni\n"
            
            if len(pending_recoveries) > 3:
                text += f"└ ...e altri {len(pending_recoveries) - 3} recuperi\n"
            text += "\n"
        
        if expired_recoveries:
            text += "❌ <b>RECUPERI SCADUTI:</b>\n"
            text += f"Hai {len(expired_recoveries)} riposi non recuperati oltre il termine!\n"
            text += "Contatta il comando per regolarizzare.\n\n"
        
        # Prossimo riposo settimanale
        next_weekly = db.query(Rest).filter(
            Rest.user_id == user.id,
            Rest.rest_type == RestType.WEEKLY,
            Rest.scheduled_date >= current_date,
            Rest.is_completed == False
        ).order_by(Rest.scheduled_date).first()
        
        if next_weekly:
            text += f"📌 Prossimo riposo settimanale: {format_date(next_weekly.scheduled_date)}\n"
            if next_weekly.scheduled_date.weekday() == 6:  # Domenica
                text += "└ ✅ Coincide con domenica\n"
        
        # Statistiche annuali
        year_stats = db.query(
            Rest.rest_type,
            func.count(Rest.id).label('total'),
            func.sum(func.cast(Rest.is_worked, Integer)).label('worked'),
            func.sum(func.cast(Rest.is_recovered, Integer)).label('recovered')
        ).filter(
            Rest.user_id == user.id,
            extract('year', Rest.scheduled_date) == current_year
        ).group_by(Rest.rest_type).all()
        
        text += f"\n📊 <b>STATISTICHE {current_year}:</b>\n"
        for stat in year_stats:
            type_name = "Riposi settimanali" if stat.rest_type == RestType.WEEKLY else "Festività"
            text += f"{type_name}: {stat.total} totali\n"
            text += f"├ Lavorati: {stat.worked or 0}\n"
            text += f"└ Recuperati: {stat.recovered or 0}\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📅 Pianifica riposo", callback_data="rest_plan"),
                InlineKeyboardButton("✅ Registra recupero", callback_data="rest_recover")
            ],
            [
                InlineKeyboardButton("📊 Report dettagliato", callback_data="rest_report"),
                InlineKeyboardButton("⚙️ Impostazioni", callback_data="rest_settings")
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

async def rest_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle rest callbacks"""
    query = update.callback_query
    action = query.data.replace("rest_", "")
    
    if action == "plan":
        await plan_rest(update, context)
    elif action == "recover":
        await register_recovery(update, context)
    elif action == "report":
        await show_rest_report(update, context)
    elif action == "settings":
        await show_rest_settings(update, context)

async def plan_rest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Plan weekly rest"""
    text = "📅 <b>PIANIFICAZIONE RIPOSO SETTIMANALE</b>\n\n"
    text += "Seleziona il giorno per il prossimo riposo:\n\n"
    text += "💡 Ricorda: deve essere fruito almeno una volta\n"
    text += "ogni 2 mesi di domenica"
    
    # Genera calendario per le prossime 2 settimane
    current_date = get_current_date()
    keyboard = []
    
    for i in range(14):
        date_option = current_date + timedelta(days=i)
        day_name = date_option.strftime('%A')
        emoji = "🟢" if date_option.weekday() == 6 else ""  # Domenica
        
        button_text = f"{emoji} {format_date(date_option)} - {day_name}"
        callback_data = f"rest_plan_{date_option.strftime('%Y%m%d')}"
        
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_rest")])
    
    await update.callback_query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def register_recovery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register rest recovery"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Lista recuperi pendenti
        pending = db.query(Rest).filter(
            Rest.user_id == user.id,
            Rest.is_worked == True,
            Rest.is_recovered == False
        ).order_by(Rest.scheduled_date).all()
        
        if not pending:
            await update.callback_query.edit_message_text(
                "✅ Non hai recuperi da registrare!",
                parse_mode='HTML',
                reply_markup=get_back_keyboard("back_to_rest")
            )
            return
        
        text = "✅ <b>REGISTRAZIONE RECUPERO RIPOSO</b>\n\n"
        text += "Seleziona il riposo che hai recuperato:\n\n"
        
        keyboard = []
        for rest in pending[:10]:
            rest_type = "Settimanale" if rest.rest_type == RestType.WEEKLY else "Festivo"
            days_ago = (get_current_date() - rest.scheduled_date).days
            
            button_text = f"{rest_type} del {format_date(rest.scheduled_date)} ({days_ago}gg fa)"
            callback_data = f"rest_recover_{rest.id}"
            
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        keyboard.append([InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_rest")])
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    finally:
        db.close()

async def show_rest_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show detailed rest report"""
    user_id = str(update.effective_user.id)
    current_year = datetime.now().year
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        text = f"📊 <b>REPORT RIPOSI {current_year}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Analisi per mese
        for month in range(1, 13):
            month_rests = db.query(Rest).filter(
                Rest.user_id == user.id,
                extract('month', Rest.scheduled_date) == month,
                extract('year', Rest.scheduled_date) == current_year
            ).all()
            
            if month_rests:
                month_name = date(current_year, month, 1).strftime('%B')
                text += f"<b>{month_name}:</b>\n"
                
                weekly = sum(1 for r in month_rests if r.rest_type == RestType.WEEKLY)
                weekly_worked = sum(1 for r in month_rests if r.rest_type == RestType.WEEKLY and r.is_worked)
                
                text += f"├ Riposi settimanali: {weekly} (lavorati: {weekly_worked})\n"
                
                holidays = sum(1 for r in month_rests if r.rest_type == RestType.HOLIDAY)
                if holidays:
                    holidays_worked = sum(1 for r in month_rests if r.rest_type == RestType.HOLIDAY and r.is_worked)
                    text += f"├ Festività: {holidays} (lavorate: {holidays_worked})\n"
                
                # Calcola indennità compensazione
                compensation_days = sum(1 for r in month_rests if r.is_worked)
                if compensation_days:
                    compensation_amount = compensation_days * 10.90  # €10.90 per giorno
                    text += f"└ Indennità compensazione: {format_currency(compensation_amount)}\n"
                
                text += "\n"
        
        # Riepilogo finale
        total_rests = db.query(Rest).filter(
            Rest.user_id == user.id,
            extract('year', Rest.scheduled_date) == current_year
        ).all()
        
        total_worked = sum(1 for r in total_rests if r.is_worked)
        total_recovered = sum(1 for r in total_rests if r.is_recovered)
        total_pending = total_worked - total_recovered
        
        text += f"<b>RIEPILOGO ANNUALE:</b>\n"
        text += f"├ Riposi totali: {len(total_rests)}\n"
        text += f"├ Lavorati: {total_worked}\n"
        text += f"├ Recuperati: {total_recovered}\n"
        text += f"├ Da recuperare: {total_pending}\n"
        text += f"└ Indennità totali: {format_currency(total_worked * 10.90)}\n"
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=get_back_keyboard("back_to_rest")
        )
        
    finally:
        db.close()

async def show_rest_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show rest settings"""
    text = "⚙️ <b>IMPOSTAZIONI RIPOSI</b>\n\n"
    text += "🚧 Funzionalità in sviluppo\n\n"
    text += "Qui potrai configurare:\n"
    text += "• Pianificazione automatica riposi\n"
    text += "• Alert per recuperi in scadenza\n"
    text += "• Preferenze giorni riposo\n"
    
    await update.callback_query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=get_back_keyboard("back_to_rest")
    )

async def check_rest_on_service_date(db, user_id: int, service_date: date) -> Rest:
    """Check if there's a planned rest on service date"""
    return db.query(Rest).filter(
        Rest.user_id == user_id,
        Rest.scheduled_date == service_date,
        Rest.is_completed == False
    ).first()

async def convert_rest_to_worked(db, rest: Rest, service_id: int, reason: str = None):
    """Convert a rest day to worked day"""
    rest.is_worked = True
    rest.is_completed = True
    rest.work_reason = reason or "Esigenze di servizio"
    rest.service_id = service_id
    rest.recovery_due_date = rest.scheduled_date + timedelta(weeks=4)
    db.commit()
