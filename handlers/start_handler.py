import logging

logger = logging.getLogger(__name__)


"""
Start command and dashboard handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database.connection import SessionLocal
from database.models import User, Service, Overtime, TravelSheet, Leave

from utils.clean_chat import register_bot_message, delete_message_after_delay
from config.settings import get_current_date, get_current_datetime
from utils.formatters import format_currency, format_date
from services.calculation_service import calculate_month_totals

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    logger.info("🚀 START COMMAND CHIAMATO!")
    logger.info(f"User: {update.effective_user.id if update.effective_user else 'Unknown'}")
    logger.info(f"Chat: {update.effective_chat.id if update.effective_chat else 'Unknown'}")
    try:
        logger.info("Start command received")
        # Gestisci sia messaggi che callback query
        if update.message:
            user = update.message.from_user
            chat_id = update.message.chat_id
            reply_func = update.message.reply_text
        elif update.callback_query:
            user = update.callback_query.from_user
            chat_id = update.callback_query.message.chat_id
            reply_func = update.callback_query.message.reply_text
            await update.callback_query.answer()
        else:
            return
    
        # Get or create user
        db = SessionLocal()
        try:
            db_user = db.query(User).filter(User.telegram_id == str(user.id)).first()
        
            if not db_user:
                # Create new user
                db_user = User(
                    telegram_id=str(user.id),
                    chat_id=str(chat_id),
                    username=user.username if user.username else "",
                    first_name=user.first_name if user.first_name else "",
                    last_name=user.last_name if user.last_name else ""
                ,
                    irpef_rate=0.27,
                    base_shift_hours=6,
                    parameter=108.5,
                    current_year_leave=32,
                    current_year_leave_used=0,
                    previous_year_leave=0)
                db.add(db_user)
                db.commit()
            
                # Send welcome message with setup
                await send_welcome_setup(update, context, db_user)
            else:
                # Update chat_id if changed
                if db_user.chat_id != str(chat_id):
                    db_user.chat_id = str(chat_id)
                    db.commit()
            
                # Send dashboard
                await send_dashboard(update, context, db_user, db)
        except Exception as e:
            print(f"Errore in start_command: {e}")
            import traceback
            traceback.print_exc()
        
            error_message = "❌ Si è verificato un errore. Riprova con /start"
            await reply_func(error_message, parse_mode='HTML')
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Errore in start_command: {e}", exc_info=True)
        if update.message:
            await update.message.reply_text("❌ Si è verificato un errore. Riprova con /start")
async def send_welcome_setup(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User):
    """Send welcome message for new users"""
    logger.info("🚀 START COMMAND CHIAMATO!")
    logger.info(f"User: {update.effective_user.id if update.effective_user else 'Unknown'}")
    logger.info(f"Chat: {update.effective_chat.id if update.effective_chat else 'Unknown'}")
    welcome_text = (
        "🎯 <b>Benvenuto in CarabinieriPayBot v3.0!</b>\n\n"
        "Il sistema definitivo per il calcolo stipendi dell'Arma.\n\n"
        "Prima di iniziare, configuriamo i tuoi dati:\n\n"
        "1️⃣ Seleziona il tuo grado\n"
        "2️⃣ Inserisci il comando di appartenenza\n"
        "3️⃣ Imposta l'aliquota IRPEF\n"
        "4️⃣ Configura le licenze residue\n\n"
        "Iniziamo! 👇"
    )
    
    keyboard = [
        [InlineKeyboardButton("⚙️ Configura ora", callback_data="setup_start")]
    ]
    
    if update.message:
        await update.message.reply_text(
            welcome_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.callback_query.message.reply_text(
            welcome_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def send_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, db: Session):
    """Send main dashboard"""
    # Verifica se l'utente è configurato
    if not user.rank or not user.command:
       # Utente non configurato, mostra setup
       await send_welcome_setup(update, context, user)
       return
   
    current_date = get_current_date()
    current_month = current_date.month
    current_year = current_date.year
    current_date = get_current_date()
    current_month = current_date.month
    current_year = current_date.year
    
    # Calculate month totals - con gestione errori
    try:
        month_data = calculate_month_totals(db, user.id, current_month, current_year)
    except:
        month_data = {
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
    
    # Get unpaid overtime
    unpaid_overtime = db.query(Overtime).filter(
        Overtime.user_id == user.id,
        Overtime.is_paid == False
    ).all()
    
    unpaid_hours = sum(ot.hours for ot in unpaid_overtime) if unpaid_overtime else 0
    unpaid_amount = sum(ot.amount for ot in unpaid_overtime) if unpaid_overtime else 0
    
    # Get unpaid travel sheets
    unpaid_sheets = db.query(TravelSheet).filter(
        TravelSheet.user_id == user.id,
        TravelSheet.is_paid == False
    ).all()
    
    sheets_count = len(unpaid_sheets) if unpaid_sheets else 0
    sheets_amount = sum(sheet.amount for sheet in unpaid_sheets) if unpaid_sheets else 0
    
    # Calculate remaining leaves
    remaining_current = user.current_year_leave - user.current_year_leave_used
    
    # Format dashboard
    dashboard_text = f"""
🏠 <b>CARABINIERI PAY BOT v3.0</b>
━━━━━━━━━━━━━━━━━━━━━━━━
Bentornato <b>{user.rank or 'Collega'} {user.first_name or ''}</b>
Comando: <b>{user.command or 'Da configurare'}</b>

💰 <b>{current_date.strftime('%B %Y').upper()}</b> (aggiornato ore {datetime.now().strftime('%H:%M')})
├ Giorni: {month_data['days_worked']}/{current_date.day} lavorati
├ Ore totali: {month_data['total_hours']:.0f}h
├ Straordinari pagati: {format_currency(month_data['paid_overtime'])} ({month_data['paid_hours']:.0f}h)
├ Straordinari da pagare: {format_currency(month_data['unpaid_overtime'])} ({month_data['unpaid_hours']:.0f}h)
├ Indennità: {format_currency(month_data['allowances'])}
├ Scorte/Missioni: {format_currency(month_data['missions'])}
└ 📊 <b>TOTALE MESE: {format_currency(month_data['total'])}</b>

⏰ <b>STRAORDINARI ACCUMULATI:</b>
├ Da gennaio: {unpaid_hours:.0f}h non pagate
├ Valore: {format_currency(unpaid_amount)}
└ Prossimo pagamento: Giugno

📋 <b>FOGLI VIAGGIO DA PAGARE:</b>
├ In attesa: {sheets_count} FV
├ Importo: {format_currency(sheets_amount)}
"""
    
    if unpaid_sheets:
        oldest_sheet = min(unpaid_sheets, key=lambda x: x.date)
        dashboard_text += f"└ ⚠️ FV più vecchio: {oldest_sheet.date.strftime('%b %Y').upper()}\n"
    else:
        dashboard_text += "└ ✅ Tutti pagati\n"
    
    dashboard_text += f"""
🏖️ <b>LICENZE RESIDUE:</b>
├ Anno {current_year}: {remaining_current} giorni
├ Anno {current_year-1}: {user.previous_year_leave} giorni
└ ⚠️ Scadenza {current_year-1}: 31/03/{current_year}
"""
    
    # Create keyboard
    keyboard = [
        [
            InlineKeyboardButton("🆕 Nuovo Servizio", callback_data="dashboard_new_service"),
            InlineKeyboardButton("🚔 Nuova Scorta", callback_data="dashboard_new_escort")
        ],
        [
            InlineKeyboardButton("📊 Report Dettagliato", callback_data="dashboard_report"),
            InlineKeyboardButton("⏰ Gestione Straordinari", callback_data="dashboard_overtime")
        ],
        [
            InlineKeyboardButton("📋 Fogli Viaggio", callback_data="dashboard_travel_sheets"),
            InlineKeyboardButton("🏖️ Gestione Licenze", callback_data="dashboard_leaves")
        ],
        [InlineKeyboardButton("⚙️ Impostazioni", callback_data="dashboard_settings")]
    ]
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            dashboard_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            dashboard_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle dashboard callbacks"""
    query = update.callback_query
    action = query.data.replace("dashboard_", "")
    
    if action == "new_service":
        from handlers.service_handler import new_service_command
        await new_service_command(update, context)
    elif action == "new_escort":
        from handlers.service_handler import new_service_command
        context.user_data['service_type'] = 'ESCORT'
        await new_service_command(update, context)
    elif action == "report":
        from handlers.report_handler import month_command
        await month_command(update, context)
    elif action == "overtime":
        from handlers.overtime_handler import overtime_command
        await overtime_command(update, context)
    elif action == "travel_sheets":
        from handlers.travel_sheet_handler import travel_sheets_command
        await travel_sheets_command(update, context)
    elif action == "leaves":
        from handlers.leave_handler import leave_command
        await leave_command(update, context)
    elif action == "settings":
        from handlers.settings_handler import settings_command
        await settings_command(update, context)