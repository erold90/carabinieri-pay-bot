"""
Export handler per generazione file Excel/PDF
"""
import pandas as pd
import io
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy import extract

from database.connection import SessionLocal
from database.models import User, Service, Overtime, TravelSheet, Leave
from utils.formatters import format_currency, format_date
from services.calculation_service import calculate_month_totals

async def generate_excel_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate complete Excel export"""
    user_id = str(update.effective_user.id)
    current_year = datetime.now().year
    
    await update.message.reply_text("📊 Generazione export in corso...")
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Crea Excel con più fogli
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            
            # 1. FOGLIO SERVIZI
            services = db.query(Service).filter(
                Service.user_id == user.id,
                extract('year', Service.date) == current_year
            ).order_by(Service.date).all()
            
            service_data = []
            for s in services:
                service_data.append({
                    'Data': s.date,
                    'Dalle': s.start_time.strftime('%H:%M'),
                    'Alle': s.end_time.strftime('%H:%M'),
                    'Ore': s.total_hours,
                    'Tipo': s.service_type.value,
                    'Festivo': 'Sì' if s.is_holiday else 'No',
                    'Super-Festivo': 'Sì' if s.is_super_holiday else 'No',
                    'Straordinari': s.overtime_amount,
                    'Indennità': s.allowances_amount,
                    'Missioni': s.mission_amount,
                    'TOTALE': s.total_amount,
                    'Note': s.destination if s.destination else ''
                })
            
            df_services = pd.DataFrame(service_data)
            df_services.to_excel(writer, sheet_name='Servizi', index=False)
            
            # 2. FOGLIO STRAORDINARI
            overtimes = db.query(Overtime).filter(
                Overtime.user_id == user.id,
                extract('year', Overtime.date) == current_year
            ).order_by(Overtime.date).all()
            
            ot_data = []
            for ot in overtimes:
                ot_data.append({
                    'Data': ot.date,
                    'Tipo': ot.overtime_type.value,
                    'Ore': ot.hours,
                    'Tariffa': ot.hourly_rate,
                    'Importo': ot.amount,
                    'Pagato': 'Sì' if ot.is_paid else 'No',
                    'Data Pagamento': ot.paid_date if ot.paid_date else ''
                })
            
            df_overtime = pd.DataFrame(ot_data)
            df_overtime.to_excel(writer, sheet_name='Straordinari', index=False)
            
            # 3. FOGLIO FOGLI VIAGGIO
            travel_sheets = db.query(TravelSheet).filter(
                TravelSheet.user_id == user.id,
                extract('year', TravelSheet.date) == current_year
            ).order_by(TravelSheet.date).all()
            
            fv_data = []
            for fv in travel_sheets:
                fv_data.append({
                    'Data': fv.date,
                    'Numero FV': fv.sheet_number,
                    'Destinazione': fv.destination,
                    'Importo': fv.amount,
                    'Pagato': 'Sì' if fv.is_paid else 'No',
                    'Data Pagamento': fv.paid_date if fv.paid_date else ''
                })
            
            df_fv = pd.DataFrame(fv_data)
            df_fv.to_excel(writer, sheet_name='Fogli Viaggio', index=False)
            
            # 4. FOGLIO RIEPILOGO MENSILE
            monthly_data = []
            for month in range(1, 13):
                month_totals = calculate_month_totals(db, user.id, month, current_year)
                if month_totals['days_worked'] > 0:
                    monthly_data.append({
                        'Mese': datetime(current_year, month, 1).strftime('%B'),
                        'Giorni Lavorati': month_totals['days_worked'],
                        'Ore Totali': month_totals['total_hours'],
                        'Straordinari Pagati': month_totals['paid_overtime'],
                        'Straordinari Non Pagati': month_totals['unpaid_overtime'],
                        'Indennità': month_totals['allowances'],
                        'Missioni': month_totals['missions'],
                        'TOTALE': month_totals['total']
                    })
            
            df_monthly = pd.DataFrame(monthly_data)
            df_monthly.to_excel(writer, sheet_name='Riepilogo Mensile', index=False)
            
            # 5. FOGLIO LICENZE
            leaves = db.query(Leave).filter(
                Leave.user_id == user.id,
                extract('year', Leave.start_date) == current_year
            ).order_by(Leave.start_date).all()
            
            leave_data = []
            for leave in leaves:
                leave_data.append({
                    'Tipo': leave.leave_type.value,
                    'Dal': leave.start_date,
                    'Al': leave.end_date,
                    'Giorni': leave.days,
                    'Note': leave.notes if leave.notes else ''
                })
            
            df_leaves = pd.DataFrame(leave_data)
            df_leaves.to_excel(writer, sheet_name='Licenze', index=False)
            
            # Formattazione
            workbook = writer.book
            for worksheet in workbook.worksheets:
                # Auto-dimensiona colonne
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
                
                # Formatta numeri come valuta
                for row in worksheet.iter_rows(min_row=2):
                    for cell in row:
                        if isinstance(cell.value, (int, float)) and 'importo' in str(worksheet.cell(1, cell.column).value).lower():
                            cell.number_format = '€ #,##0.00'
        
        output.seek(0)
        
        # Invia file
        filename = f"CarabinieriPay_{user.rank}_{current_year}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        await update.message.reply_document(
            document=output,
            filename=filename,
            caption=f"📊 Export completo anno {current_year}\n\n"
                   f"Contiene:\n"
                   f"✅ Dettaglio servizi\n"
                   f"✅ Straordinari con stato pagamento\n"
                   f"✅ Fogli viaggio\n"
                   f"✅ Riepilogo mensile\n"
                   f"✅ Gestione licenze\n\n"
                   f"📱 Pronto per il commercialista!"
        )
        
    finally:
        db.close()
