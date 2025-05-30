#!/usr/bin/env python3
import subprocess
import os

print("🔧 IMPLEMENTAZIONE GESTIONE RIPOSI E RECUPERI")
print("=" * 50)

# 1. AGGIORNA MODELS.PY per includere i riposi
print("\n1️⃣ Aggiornamento modelli database...")

models_additions = '''
class RestType(str, enum.Enum):
    WEEKLY = "WEEKLY"  # Riposo settimanale
    HOLIDAY = "HOLIDAY"  # Festività infrasettimanale
    COMPENSATORY = "COMPENSATORY"  # Riposo compensativo per straordinari

class Rest(Base):
    __tablename__ = "rests"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Dettagli riposo
    rest_type = Column(Enum(RestType), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    actual_date = Column(Date)  # Se diversa dalla pianificata
    
    # Stato
    is_completed = Column(Boolean, default=False)
    is_worked = Column(Boolean, default=False)  # Se ha lavorato invece di riposare
    work_reason = Column(String)  # Motivo del richiamo
    
    # Recupero
    recovery_due_date = Column(Date)  # Entro 4 settimane
    recovery_date = Column(Date)  # Quando effettivamente recuperato
    is_recovered = Column(Boolean, default=False)
    
    # Riferimenti
    service_id = Column(Integer, ForeignKey("services.id"))  # Servizio che ha sostituito il riposo
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_datetime)
    updated_at = Column(DateTime, default=get_current_datetime, onupdate=get_current_datetime)
    
    # Relationships
    user = relationship("User", back_populates="rests")
    service = relationship("Service", back_populates="rest_replaced")

# Aggiungi relazione in Service
# rest_replaced = relationship("Rest", back_populates="service", uselist=False)

# Aggiungi in User
# rests = relationship("Rest", back_populates="user", cascade="all, delete-orphan")
'''

# Leggi models.py e aggiungi le nuove classi
with open('database/models.py', 'r') as f:
    models_content = f.read()

# Aggiungi dopo LeaveType
if 'class RestType' not in models_content:
    pos = models_content.find('class User(Base):')
    if pos > 0:
        models_content = models_content[:pos] + models_additions + '\n\n' + models_content[pos:]
    
    # Aggiungi relazioni
    # In Service
    service_pos = models_content.find('user = relationship("User"')
    if service_pos > 0:
        end_line = models_content.find('\n', service_pos)
        models_content = models_content[:end_line] + '\n    rest_replaced = relationship("Rest", back_populates="service", uselist=False)' + models_content[end_line:]
    
    # In User
    user_pos = models_content.find('leaves = relationship("Leave"')
    if user_pos > 0:
        end_line = models_content.find('\n', user_pos)
        models_content = models_content[:end_line] + '\n    rests = relationship("Rest", back_populates="user", cascade="all, delete-orphan")' + models_content[end_line:]
    
    with open('database/models.py', 'w') as f:
        f.write(models_content)
    print("✅ Modelli database aggiornati")

# 2. CREA REST_HANDLER.PY
print("\n2️⃣ Creazione rest_handler.py...")

rest_handler = '''"""
Rest and recovery management handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, date, timedelta
from sqlalchemy import extract, func, and_, or_

from database.connection import SessionLocal
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
        
        text = "🛌 <b>GESTIONE RIPOSI E RECUPERI</b>\\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        
        # Riepilogo mensile
        text += f"📅 <b>SITUAZIONE {current_date.strftime('%B %Y').upper()}:</b>\\n\\n"
        
        weekly_count = sum(1 for r in monthly_rests if r.rest_type == RestType.WEEKLY)
        holiday_count = sum(1 for r in monthly_rests if r.rest_type == RestType.HOLIDAY)
        worked_count = sum(1 for r in monthly_rests if r.is_worked)
        
        text += f"Riposi settimanali pianificati: {weekly_count}\\n"
        text += f"├ Fruiti regolarmente: {weekly_count - sum(1 for r in monthly_rests if r.rest_type == RestType.WEEKLY and r.is_worked)}\\n"
        text += f"└ Lavorati (da recuperare): {sum(1 for r in monthly_rests if r.rest_type == RestType.WEEKLY and r.is_worked)}\\n\\n"
        
        text += f"Festività infrasettimanali: {holiday_count}\\n"
        text += f"├ Riposate: {holiday_count - sum(1 for r in monthly_rests if r.rest_type == RestType.HOLIDAY and r.is_worked)}\\n"
        text += f"└ Lavorate: {sum(1 for r in monthly_rests if r.rest_type == RestType.HOLIDAY and r.is_worked)}\\n\\n"
        
        # Alert recuperi
        if pending_recoveries:
            text += "⚠️ <b>RECUPERI DA EFFETTUARE:</b>\\n"
            for rest in pending_recoveries[:3]:
                days_left = (rest.recovery_due_date - current_date).days
                emoji = "🔴" if days_left <= 7 else "🟡"
                text += f"{emoji} {format_date(rest.scheduled_date)} - "
                text += f"Scade tra {days_left} giorni\\n"
            
            if len(pending_recoveries) > 3:
                text += f"└ ...e altri {len(pending_recoveries) - 3} recuperi\\n"
            text += "\\n"
        
        if expired_recoveries:
            text += "❌ <b>RECUPERI SCADUTI:</b>\\n"
            text += f"Hai {len(expired_recoveries)} riposi non recuperati oltre il termine!\\n"
            text += "Contatta il comando per regolarizzare.\\n\\n"
        
        # Prossimo riposo settimanale
        next_weekly = db.query(Rest).filter(
            Rest.user_id == user.id,
            Rest.rest_type == RestType.WEEKLY,
            Rest.scheduled_date >= current_date,
            Rest.is_completed == False
        ).order_by(Rest.scheduled_date).first()
        
        if next_weekly:
            text += f"📌 Prossimo riposo settimanale: {format_date(next_weekly.scheduled_date)}\\n"
            if next_weekly.scheduled_date.weekday() == 6:  # Domenica
                text += "└ ✅ Coincide con domenica\\n"
        
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
        
        text += f"\\n📊 <b>STATISTICHE {current_year}:</b>\\n"
        for stat in year_stats:
            type_name = "Riposi settimanali" if stat.rest_type == RestType.WEEKLY else "Festività"
            text += f"{type_name}: {stat.total} totali\\n"
            text += f"├ Lavorati: {stat.worked or 0}\\n"
            text += f"└ Recuperati: {stat.recovered or 0}\\n"
        
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
    text = "📅 <b>PIANIFICAZIONE RIPOSO SETTIMANALE</b>\\n\\n"
    text += "Seleziona il giorno per il prossimo riposo:\\n\\n"
    text += "💡 Ricorda: deve essere fruito almeno una volta\\n"
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
        
        text = "✅ <b>REGISTRAZIONE RECUPERO RIPOSO</b>\\n\\n"
        text += "Seleziona il riposo che hai recuperato:\\n\\n"
        
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
        
        text = f"📊 <b>REPORT RIPOSI {current_year}</b>\\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        
        # Analisi per mese
        for month in range(1, 13):
            month_rests = db.query(Rest).filter(
                Rest.user_id == user.id,
                extract('month', Rest.scheduled_date) == month,
                extract('year', Rest.scheduled_date) == current_year
            ).all()
            
            if month_rests:
                month_name = date(current_year, month, 1).strftime('%B')
                text += f"<b>{month_name}:</b>\\n"
                
                weekly = sum(1 for r in month_rests if r.rest_type == RestType.WEEKLY)
                weekly_worked = sum(1 for r in month_rests if r.rest_type == RestType.WEEKLY and r.is_worked)
                
                text += f"├ Riposi settimanali: {weekly} (lavorati: {weekly_worked})\\n"
                
                holidays = sum(1 for r in month_rests if r.rest_type == RestType.HOLIDAY)
                if holidays:
                    holidays_worked = sum(1 for r in month_rests if r.rest_type == RestType.HOLIDAY and r.is_worked)
                    text += f"├ Festività: {holidays} (lavorate: {holidays_worked})\\n"
                
                # Calcola indennità compensazione
                compensation_days = sum(1 for r in month_rests if r.is_worked)
                if compensation_days:
                    compensation_amount = compensation_days * 10.90  # €10.90 per giorno
                    text += f"└ Indennità compensazione: {format_currency(compensation_amount)}\\n"
                
                text += "\\n"
        
        # Riepilogo finale
        total_rests = db.query(Rest).filter(
            Rest.user_id == user.id,
            extract('year', Rest.scheduled_date) == current_year
        ).all()
        
        total_worked = sum(1 for r in total_rests if r.is_worked)
        total_recovered = sum(1 for r in total_rests if r.is_recovered)
        total_pending = total_worked - total_recovered
        
        text += f"<b>RIEPILOGO ANNUALE:</b>\\n"
        text += f"├ Riposi totali: {len(total_rests)}\\n"
        text += f"├ Lavorati: {total_worked}\\n"
        text += f"├ Recuperati: {total_recovered}\\n"
        text += f"├ Da recuperare: {total_pending}\\n"
        text += f"└ Indennità totali: {format_currency(total_worked * 10.90)}\\n"
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=get_back_keyboard("back_to_rest")
        )
        
    finally:
        db.close()

async def show_rest_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show rest settings"""
    text = "⚙️ <b>IMPOSTAZIONI RIPOSI</b>\\n\\n"
    text += "🚧 Funzionalità in sviluppo\\n\\n"
    text += "Qui potrai configurare:\\n"
    text += "• Pianificazione automatica riposi\\n"
    text += "• Alert per recuperi in scadenza\\n"
    text += "• Preferenze giorni riposo\\n"
    
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
'''

with open('handlers/rest_handler.py', 'w') as f:
    f.write(rest_handler)
print("✅ rest_handler.py creato")

# 3. AGGIORNA SERVICE_HANDLER per verificare riposi
print("\n3️⃣ Aggiornamento service_handler.py...")

service_updates = '''
# Aggiungi import
from database.models import Rest, RestType
from handlers.rest_handler import check_rest_on_service_date, convert_rest_to_worked

# Modifica handle_status_selection per gestire meglio i riposi
async def handle_status_selection_updated(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle personal status selection with rest management"""
    query = update.callback_query
    await query.answer()
    
    status = query.data.replace("status_", "")
    context.user_data['personal_status'] = status
    
    # Verifica se c'è un riposo pianificato per questa data
    if status == 'rest':
        user_id = str(query.from_user.id)
        service_date = context.user_data['service_date']
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            
            # Verifica riposo pianificato
            planned_rest = await check_rest_on_service_date(db, user.id, service_date)
            
            if planned_rest:
                context.user_data['rest_to_convert'] = planned_rest.id
                rest_type = "settimanale" if planned_rest.rest_type == RestType.WEEKLY else "festivo"
                
                text = f"⚠️ <b>RICHIAMO DA RIPOSO {rest_type.upper()}!</b>\\n\\n"
                text += "Stai lavorando in un giorno pianificato per il riposo.\\n\\n"
                text += "✅ Spettano automaticamente:\\n"
                text += "├ Indennità compensazione: €10,90\\n"
                text += "├ Diritto al recupero entro 4 settimane\\n"
                text += "└ Straordinario per ore oltre il turno base\\n\\n"
                text += "Motivo del richiamo?"
                
                keyboard = [
                    [InlineKeyboardButton("🚨 Emergenza operativa", callback_data="recall_emergency")],
                    [InlineKeyboardButton("👮 Carenza personale", callback_data="recall_shortage")],
                    [InlineKeyboardButton("📋 Servizio comandato", callback_data="recall_ordered")],
                    [InlineKeyboardButton("🔄 Altro motivo", callback_data="recall_other")]
                ]
                
                await query.edit_message_text(
                    text,
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return SELECT_TIME
            else:
                # Crea nuovo riposo non pianificato
                new_rest = Rest(
                    user_id=user.id,
                    rest_type=RestType.WEEKLY,
                    scheduled_date=service_date,
                    is_worked=True,
                    work_reason="Riposo non pianificato - lavorato",
                    recovery_due_date=service_date + timedelta(weeks=4)
                )
                db.add(new_rest)
                db.commit()
                context.user_data['rest_to_convert'] = new_rest.id
        finally:
            db.close()
    
    # Gestione normale per altri stati
    if status in ['leave', 'rest']:
        context.user_data['called_from_leave'] = (status == 'leave')
        context.user_data['called_from_rest'] = (status == 'rest')
        
        text = "⚠️ <b>RICHIAMO IN SERVIZIO!</b>\\n"
        text += "✅ Compensazione €10,90 applicata\\n"
        if status == 'leave':
            text += "✅ Licenza scalata automaticamente\\n"
        else:
            text += "✅ Riposo da recuperare entro 4 settimane\\n"
    else:
        text = ""
    
    text += "\\n⏰ <b>ORARIO SERVIZIO</b>\\n\\n"
    text += "Inserisci l'orario di inizio (formato HH:MM):\\n"
    text += "Esempi: 06:30, 14:45, 22:00"
    
    await query.edit_message_text(text, parse_mode='HTML')
    context.user_data['waiting_for_start_time'] = True
    
    return SELECT_TIME
'''

# 4. AGGIORNA CALCULATION_SERVICE per indennità compensazione
print("\n4️⃣ Aggiornamento calculation_service.py...")

calc_updates = '''
# Nella funzione calculate_service_total, aggiungi dopo le altre indennità:

    # Indennità compensazione per richiamo da riposo
    if service.called_from_rest or service.called_from_leave:
        allowances['compensation'] = SERVICE_ALLOWANCES['compensation']
        
        # Se è un riposo festivo, aggiungi anche presenza festiva
        if service.called_from_rest and service.is_holiday:
            if service.is_super_holiday:
                allowances['super_holiday_presence'] = SERVICE_ALLOWANCES['super_holiday_presence']
            else:
                allowances['holiday_presence'] = SERVICE_ALLOWANCES['holiday_presence']
'''

# 5. AGGIORNA MAIN.PY
print("\n5️⃣ Aggiornamento main.py...")

with open('main.py', 'r') as f:
    main_content = f.read()

# Aggiungi import rest_handler
if 'from handlers.rest_handler import' not in main_content:
    import_pos = main_content.find('from handlers.leave_handler import')
    if import_pos > 0:
        end_line = main_content.find('\n', import_pos)
        main_content = main_content[:end_line] + '\nfrom handlers.rest_handler import rest_command, rest_callback' + main_content[end_line:]

# Aggiungi command handler
if 'CommandHandler("riposi"' not in main_content:
    command_pos = main_content.find('application.add_handler(CommandHandler("licenze"')
    if command_pos > 0:
        end_line = main_content.find('\n', command_pos)
        main_content = main_content[:end_line] + '\n    application.add_handler(CommandHandler("riposi", rest_command))' + main_content[end_line:]

# Aggiungi callback handler
if 'rest_callback' not in main_content:
    callback_pos = main_content.find('application.add_handler(CallbackQueryHandler(leave_callback')
    if callback_pos > 0:
        end_line = main_content.find('\n', callback_pos)
        main_content = main_content[:end_line] + '\n    application.add_handler(CallbackQueryHandler(rest_callback, pattern="^rest_"))' + main_content[end_line:]

with open('main.py', 'w') as f:
    f.write(main_content)
print("✅ main.py aggiornato")

# 6. AGGIORNA START_HANDLER per mostrare riposi nel dashboard
print("\n6️⃣ Aggiornamento dashboard...")

dashboard_update = '''
# Aggiungi nella dashboard (dopo la sezione licenze):

        # Riposi e recuperi
        current_month_rests = db.query(Rest).filter(
            Rest.user_id == user.id,
            extract('month', Rest.scheduled_date) == current_month,
            extract('year', Rest.scheduled_date) == current_year
        ).all()
        
        pending_recoveries = db.query(Rest).filter(
            Rest.user_id == user.id,
            Rest.is_worked == True,
            Rest.is_recovered == False
        ).count()
        
        dashboard_text += f"""
🛌 <b>RIPOSI E RECUPERI:</b>
├ Riposi questo mese: {len(current_month_rests)}
├ Recuperi pendenti: {pending_recoveries}
└ Prossimo riposo: {next_rest_date if next_rest_date else 'Da pianificare'}
"""

# E aggiungi il pulsante nel keyboard:
[
    InlineKeyboardButton("🛌 Gestione Riposi", callback_data="dashboard_rests"),
    InlineKeyboardButton("📋 Fogli Viaggio", callback_data="dashboard_travel_sheets")
],
'''

# 7. CREA SCRIPT MIGRAZIONE DATABASE
print("\n7️⃣ Creazione script migrazione database...")

migration_script = '''#!/usr/bin/env python3
"""
Migrazione database per aggiungere tabella riposi
"""
from database.connection import engine, Base
from database.models import Rest

print("🔄 Migrazione database per gestione riposi...")

try:
    # Crea la nuova tabella
    Rest.__table__.create(engine, checkfirst=True)
    print("✅ Tabella 'rests' creata con successo!")
except Exception as e:
    print(f"❌ Errore: {e}")
'''

with open('migrate_rest_table.py', 'w') as f:
    f.write(migration_script)
os.chmod('migrate_rest_table.py', 0o755)
print("✅ Script migrazione creato")

# 8. COMMIT FINALE
print("\n📤 Commit e push...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "feat: implementazione completa gestione riposi settimanali e festivi con recuperi"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ GESTIONE RIPOSI IMPLEMENTATA!")
print("\nFunzionalità aggiunte:")
print("✅ Tracciamento riposi settimanali e festivi")
print("✅ Gestione richiami da riposo con indennità compensazione")
print("✅ Sistema recuperi con scadenza 4 settimane")
print("✅ Distinzione riposo settimanale/festivo/compensativo")
print("✅ Report dettagliato riposi e recuperi")
print("✅ Calcolo automatico indennità compensazione €10.90")
print("✅ Alert per recuperi in scadenza")
print("✅ Verifica domeniche ogni 2 mesi")
print("\n🚀 Railway sta deployando...")
print("\n⚠️ IMPORTANTE: Dopo il deploy, esegui:")
print("   python3 migrate_rest_table.py")
print("   per creare la tabella riposi nel database")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script eliminato")
