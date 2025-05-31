"""
Report generation handler
"""
from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta, date
from sqlalchemy import extract, func
import io
import pandas as pd

from database.connection import SessionLocal, get_db
from database.models import User, Service, Overtime, TravelSheet, Leave

from utils.clean_chat import register_bot_message, delete_message_after_delay
from config.settings import get_current_date
from utils.formatters import format_currency, format_date, format_hours, format_month_year
from services.calculation_service import calculate_month_totals

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's summary"""
    await show_day_report(update, context, get_current_date())

async def yesterday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show yesterday's summary"""
    yesterday = get_current_date() - timedelta(days=1)
    await show_day_report(update, context, yesterday)

async def show_day_report(update: Update, context: ContextTypes.DEFAULT_TYPE, report_date: date):
    """Show report for a specific day"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get service for the day
        service = db.query(Service).filter(
            Service.user_id == user.id,
            Service.date == report_date
        ).first()
        
        text = f"📊 <b>RIEPILOGO {format_date(report_date).upper()}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if service:
            # Service details
            text += f"✅ <b>SERVIZIO EFFETTUATO</b>\n"
            text += f"├ Orario: {service.start_time.strftime('%H:%M')} - {service.end_time.strftime('%H:%M')}\n"
            text += f"├ Ore totali: {service.total_hours:.0f}h\n"
            text += f"├ Tipo: {service.service_type.value}\n"
            
            if service.is_double_shift:
                text += "├ ⚠️ Doppio turno\n"
            
            if service.called_from_leave or service.called_from_rest:
                text += "├ 📍 Richiamato in servizio\n"
            
            text += f"└ Totale: {format_currency(service.total_amount)}\n\n"
            
            # Breakdown
            if service.overtime_amount > 0:
                text += f"💰 Straordinari: {format_currency(service.overtime_amount)}\n"
            if service.allowances_amount > 0:
                text += f"🎖️ Indennità: {format_currency(service.allowances_amount)}\n"
            if service.mission_amount > 0:
                text += f"🚗 Missione: {format_currency(service.mission_amount)}\n"
        else:
            # Check if on leave
            leave = db.query(Leave).filter(
                Leave.user_id == user.id,
                Leave.start_date <= report_date,
                Leave.end_date >= report_date,
                Leave.is_cancelled == False
            ).first()
            
            if leave:
                text += "🏖️ <b>IN LICENZA</b>\n"
                text += f"Tipo: {leave.leave_type.value}\n"
            else:
                text += "❌ <b>Nessun servizio registrato</b>\n"
                text += "\nUsa /nuovo per registrare il servizio"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
        db.close()

async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show weekly report"""
    current_date = get_current_date()
    # Get Monday of current week
    monday = current_date - timedelta(days=current_date.weekday())
    sunday = monday + timedelta(days=6)
    
    await show_period_report(update, context, monday, sunday, "SETTIMANA")

async def month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show monthly report"""
    current_date = get_current_date()
    await show_month_report_detailed(update, context, current_date.month, current_date.year)

async def year_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show yearly report"""
    current_year = datetime.now().year
    await show_year_report(update, context, current_year)

async def show_period_report(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                            start_date: date, end_date: date, period_name: str):
    """Show report for a period"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get services in period
        services = db.query(Service).filter(
            Service.user_id == user.id,
            Service.date >= start_date,
            Service.date <= end_date
        ).order_by(Service.date).all()
        
        text = f"📊 <b>REPORT {period_name}</b>\n"
        text += f"{format_date(start_date)} - {format_date(end_date)}\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        if services:
            # Calculate totals
            total_hours = sum(s.total_hours for s in services)
            total_overtime = sum(s.overtime_amount for s in services)
            total_allowances = sum(s.allowances_amount for s in services)
            total_missions = sum(s.mission_amount for s in services)
            total_amount = sum(s.total_amount for s in services)
            
            text += f"📅 Giorni lavorati: {len(services)}\n"
            text += f"⏰ Ore totali: {total_hours:.0f}h\n"
            text += f"💰 Straordinari: {format_currency(total_overtime)}\n"
            text += f"🎖️ Indennità: {format_currency(total_allowances)}\n"
            text += f"🚗 Missioni: {format_currency(total_missions)}\n"
            text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
            text += f"💶 <b>TOTALE: {format_currency(total_amount)}</b>\n\n"
            
            # Daily breakdown
            text += "<b>DETTAGLIO GIORNALIERO:</b>\n"
            for service in services:
                text += f"├ {format_date(service.date)} - "
                text += f"{service.total_hours:.0f}h - "
                text += f"{format_currency(service.total_amount)}\n"
        else:
            text += "❌ Nessun servizio registrato nel periodo"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
        db.close()

async def show_month_report_detailed(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                   month: int, year: int):
    """Show detailed monthly report"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get month data
        month_data = calculate_month_totals(db, user.id, month, year)
        
        # Get services
        services = db.query(Service).filter(
            Service.user_id == user.id,
            extract('month', Service.date) == month,
            extract('year', Service.date) == year
        ).order_by(Service.date).all()
        
        # Get unpaid overtime (all time)
        unpaid_overtime = db.query(Overtime).filter(
            Overtime.user_id == user.id,
            Overtime.is_paid == False
        ).all()
        
        unpaid_hours = sum(ot.hours for ot in unpaid_overtime)
        unpaid_amount = sum(ot.amount for ot in unpaid_overtime)
        
        # Get unpaid travel sheets
        unpaid_sheets = db.query(TravelSheet).filter(
            TravelSheet.user_id == user.id,
            TravelSheet.is_paid == False
        ).all()
        
        # Format report
        text = f"📊 <b>REPORT {format_month_year(date(year, month, 1)).upper()} ULTRA-DETTAGLIATO</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Service statistics
        text += "📅 <b>STATISTICHE SERVIZIO</b>\n"
        text += f"├ Giorni lavorati: {month_data['days_worked']}/{date(year, month, 1).replace(day=28).day}\n"
        text += f"├ Ore totali: {month_data['total_hours']:.0f}h "
        
        if month_data['days_worked'] > 0:
            avg_hours = month_data['total_hours'] / month_data['days_worked']
            text += f"({avg_hours:.1f}h/giorno)\n"
        else:
            text += "\n"
        
        # Count special days
        double_shifts = sum(1 for s in services if s.is_double_shift)
        holidays = sum(1 for s in services if s.is_holiday and not s.is_super_holiday)
        super_holidays = sum(1 for s in services if s.is_super_holiday)
        escorts = sum(1 for s in services if s.service_type.value == "ESCORT")
        
        text += f"├ Turni >12h (doppi): {double_shifts} giorni\n"
        text += f"├ Festivi normali: {holidays}\n"
        text += f"├ SUPER-festivi: {super_holidays}\n"
        text += f"├ Servizi scorta: {escorts}\n"
        
        # Calculate total km
        total_km = sum(s.km_total for s in services if s.km_total)
        text += f"└ Km totali: {total_km:,}\n\n"
        
        # Overtime analysis
        text += f"💰 <b>ANALISI STRAORDINARI DETTAGLIATA ({month_data['paid_hours'] + month_data['unpaid_hours']:.0f}h)</b>\n"
        text += f"PAGATI QUESTO MESE ({month_data['paid_hours']:.0f}h):\n"
        
        # Get overtime by type for this month
        month_overtime = db.query(
            Overtime.overtime_type,
            func.sum(Overtime.hours).label('hours'),
            func.sum(Overtime.amount).label('amount')
        ).filter(
            Overtime.user_id == user.id,
            extract('month', Overtime.date) == month,
            extract('year', Overtime.date) == year,
            Overtime.is_paid == True
        ).group_by(Overtime.overtime_type).all()
        
        for ot in month_overtime:
            text += f"├ {ot.overtime_type.value}: {ot.hours:.0f}h = {format_currency(ot.amount)}\n"
        
        text += f"└ Totale pagato: {format_currency(month_data['paid_overtime'])}\n\n"
        
        text += f"NON PAGATI ({month_data['unpaid_hours']:.0f}h) - ACCUMULATI:\n"
        # Similar for unpaid...
        
        text += f"\nSTORICO ACCUMULO {year}:\n"
        text += f"├ Ore totali accumulate: {unpaid_hours:.0f}h\n"
        text += f"├ Valore totale: {format_currency(unpaid_amount)}\n"
        text += f"└ Prossimo pagamento: GIUGNO {year}\n\n"
        
        # Allowances
        text += "🎖️ <b>INDENNITÀ NETTE</b>\n"
        # TODO: Break down allowances by type
        text += f"└ Totale indennità: {format_currency(month_data['allowances'])}\n\n"
        
        # Missions
        text += "🚔 <b>SCORTE E MISSIONI</b>\n"
        text += f"└ Totale: {format_currency(month_data['missions'])}\n\n"
        
        # Travel sheets
        text += "📋 <b>FOGLI VIAGGIO</b>\n"
        month_sheets = [s for s in unpaid_sheets if s.date.month == month and s.date.year == year]
        text += f"├ FV di {format_month_year(date(year, month, 1))}: {len(month_sheets)} fogli\n"
        text += f"├ Importo FV mese: {format_currency(sum(s.amount for s in month_sheets))}\n"
        text += f"├ FV totali in attesa: {len(unpaid_sheets)}\n"
        text += f"└ Importo totale atteso: {format_currency(sum(s.amount for s in unpaid_sheets))}\n\n"
        
        # Leaves
        leaves = db.query(Leave).filter(
            Leave.user_id == user.id,
            extract('month', Leave.start_date) == month,
            extract('year', Leave.start_date) == year
        ).all()
        
        if leaves:
            text += "🏖️ <b>MOVIMENTI LICENZE</b>\n"
            leave_days = sum(l.days for l in leaves)
            text += f"└ Licenze utilizzate: {leave_days} giorni\n\n"
        
        # Summary
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"💶 <b>TOTALE PAGATO MESE: {format_currency(month_data['total'])}</b>\n"
        text += f"💰 DA RICEVERE (accumulo): {format_currency(month_data['unpaid_overtime'])}\n"
        text += f"📋 FV DA RICEVERE: {format_currency(sum(s.amount for s in unpaid_sheets))}\n\n"
        
        # Comparison with previous month
        if month > 1:
            prev_month_data = calculate_month_totals(db, user.id, month - 1, year)
            diff = month_data['total'] - prev_month_data['total']
            perc = (diff / prev_month_data['total'] * 100) if prev_month_data['total'] > 0 else 0
            
            text += f"📈 Confronto {format_month_year(date(year, month - 1, 1))}: "
            if diff > 0:
                text += f"+{format_currency(diff)} (+{perc:.1f}%)\n"
            else:
                text += f"{format_currency(diff)} ({perc:.1f}%)\n"
        
        # Daily average
        if month_data['days_worked'] > 0:
            daily_avg = month_data['total'] / month_data['days_worked']
            text += f"💡 Media giornaliera: {format_currency(daily_avg)}\n"
            
            # Annual projection
            annual_projection = daily_avg * 250  # Assuming 250 working days
            text += f"🎯 Proiezione annua (con accumuli): {format_currency(annual_projection)}"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
        db.close()

async def show_year_report(update: Update, context: ContextTypes.DEFAULT_TYPE, year: int):
    """Show yearly report"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get year totals
        services = db.query(Service).filter(
            Service.user_id == user.id,
            extract('year', Service.date) == year
        ).all()
        
        if not services:
            await update.message.reply_text(
                f"❌ Nessun dato per l'anno {year}",
                parse_mode='HTML'
            )
            return
        
        text = f"📊 <b>REPORT ANNUALE {year}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Calculate totals
        total_days = len(services)
        total_hours = sum(s.total_hours for s in services)
        total_overtime = sum(s.overtime_amount for s in services)
        total_allowances = sum(s.allowances_amount for s in services)
        total_missions = sum(s.mission_amount for s in services)
        total_amount = sum(s.total_amount for s in services)
        
        text += f"📅 Giorni lavorati: {total_days}\n"
        text += f"⏰ Ore totali: {total_hours:.0f}h\n"
        text += f"💰 Straordinari: {format_currency(total_overtime)}\n"
        text += f"🎖️ Indennità: {format_currency(total_allowances)}\n"
        text += f"🚗 Missioni: {format_currency(total_missions)}\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        text += f"💶 <b>TOTALE ANNO: {format_currency(total_amount)}</b>\n\n"
        
        # Monthly breakdown
        text += "<b>RIEPILOGO MENSILE:</b>\n"
        
        for month in range(1, 13):
            month_services = [s for s in services if s.date.month == month]
            if month_services:
                month_total = sum(s.total_amount for s in month_services)
                month_name = date(year, month, 1).strftime("%B")
                text += f"├ {month_name}: {format_currency(month_total)}\n"
        
        # Averages
        text += f"\n<b>MEDIE:</b>\n"
        text += f"├ Media mensile: {format_currency(total_amount / 12)}\n"
        text += f"├ Media giornaliera: {format_currency(total_amount / total_days)}\n"
        text += f"└ Ore medie/giorno: {total_hours / total_days:.1f}h\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
        db.close()

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export data to Excel"""
    user_id = str(update.effective_user.id)
    
    await update.message.reply_text(
        "📤 Generazione export in corso...",
        parse_mode='HTML'
    )
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get current year data
        current_year = datetime.now().year
        services = db.query(Service).filter(
            Service.user_id == user.id,
            extract('year', Service.date) == current_year
        ).order_by(Service.date).all()
        
        # Create DataFrame
        data = []
        for service in services:
            data.append({
                'Data': service.date,
                'Orario': f"{service.start_time.strftime('%H:%M')}-{service.end_time.strftime('%H:%M')}",
                'Ore': service.total_hours,
                'Tipo': service.service_type.value,
                'Straordinari': service.overtime_amount,
                'Indennità': service.allowances_amount,
                'Missioni': service.mission_amount,
                'Totale': service.total_amount,
                'Note': 'Doppio turno' if service.is_double_shift else ''
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Services sheet
            df.to_excel(writer, sheet_name='Servizi', index=False)
            
            # Monthly summary sheet
            monthly_summary = []
            for month in range(1, 13):
                month_data = calculate_month_totals(db, user.id, month, current_year)
                if month_data['days_worked'] > 0:
                    monthly_summary.append({
                        'Mese': date(current_year, month, 1).strftime('%B %Y'),
                        'Giorni': month_data['days_worked'],
                        'Ore': month_data['total_hours'],
                        'Straordinari Pagati': month_data['paid_overtime'],
                        'Straordinari Non Pagati': month_data['unpaid_overtime'],
                        'Indennità': month_data['allowances'],
                        'Missioni': month_data['missions'],
                        'Totale': month_data['total']
                    })
            
            df_monthly = pd.DataFrame(monthly_summary)
            df_monthly.to_excel(writer, sheet_name='Riepilogo Mensile', index=False)
            
            # Format columns
            workbook = writer.book
            for worksheet in workbook.worksheets:
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
        output.seek(0)
        
        # Send file
        await update.message.reply_document(
            document=output,
            filename=f"CarabinieriPay_Export_{current_year}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            caption=f"📊 Export dati {current_year}\n\nContiene:\n- Dettaglio servizi\n- Riepilogo mensile\n- Statistiche"
        )
        
        db.close()