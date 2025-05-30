#!/usr/bin/env python3
import os

print("🔧 Fix travel_sheet_handler.py vuoto")

# Contenuto del handler
handler_content = '''"""
Travel sheet management handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
from sqlalchemy import extract, func, and_, or_

from database.connection import SessionLocal
from database.models import User, TravelSheet, Service
from config.settings import get_current_date, PAYMENT_DETAILS
from utils.formatters import format_currency, format_date, format_travel_sheet_summary
from utils.keyboards import get_back_keyboard

async def travel_sheets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show travel sheets dashboard"""
    user_id = str(update.effective_user.id)
    current_date = get_current_date()
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get all travel sheets
        sheets = db.query(TravelSheet).filter(
            TravelSheet.user_id == user.id
        ).order_by(TravelSheet.date.desc()).all()
        
        # Separate paid and unpaid
        unpaid_sheets = [s for s in sheets if not s.is_paid]
        paid_sheets = [s for s in sheets if s.is_paid]
        
        # Calculate totals
        unpaid_total = sum(s.amount for s in unpaid_sheets)
        paid_total = sum(s.amount for s in paid_sheets)
        
        # Check for old unpaid sheets
        old_sheets = []
        for sheet in unpaid_sheets:
            days_waiting = (current_date - sheet.date).days
            if days_waiting > 90:
                old_sheets.append((sheet, days_waiting))
        
        text = "📋 <b>GESTIONE FOGLI VIAGGIO</b>\\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        
        # Summary
        text += "📊 <b>RIEPILOGO:</b>\\n"
        text += f"├ FV totali: {len(sheets)}\\n"
        text += f"├ Da pagare: {len(unpaid_sheets)} ({format_currency(unpaid_total)})\\n"
        text += f"└ Già pagati: {len(paid_sheets)} ({format_currency(paid_total)})\\n\\n"
        
        # Alerts
        if old_sheets:
            text += "⚠️ <b>ALERT PAGAMENTI:</b>\\n"
            for sheet, days in old_sheets[:3]:
                text += f"├ F.V. {sheet.sheet_number}: {days} giorni!\\n"
            if len(old_sheets) > 3:
                text += f"└ ...e altri {len(old_sheets) - 3} FV\\n"
            text += "\\n"
        
        # Recent unpaid
        if unpaid_sheets:
            text += "📌 <b>ULTIMI FV DA PAGARE:</b>\\n"
            for sheet in unpaid_sheets[:5]:
                days_waiting = (current_date - sheet.date).days
                text += f"├ {format_date(sheet.date)} - FV {sheet.sheet_number}\\n"
                text += f"│ └ {sheet.destination} - {format_currency(sheet.amount)} ({days_waiting}gg)\\n"
            
            if len(unpaid_sheets) > 5:
                text += f"└ ...e altri {len(unpaid_sheets) - 5} fogli\\n"
        else:
            text += "✅ Tutti i fogli viaggio sono stati pagati!\\n"
        
        # Statistics
        if sheets:
            avg_payment_time = sum((s.paid_date - s.date).days for s in paid_sheets if s.paid_date) / len(paid_sheets) if paid_sheets else 0
            text += f"\\n📈 <b>STATISTICHE:</b>\\n"
            text += f"├ Tempo medio pagamento: {avg_payment_time:.0f} giorni\\n"
            text += f"└ Importo medio FV: {format_currency(sum(s.amount for s in sheets) / len(sheets))}\\n"
        
        keyboard = [
            [
                InlineKeyboardButton("📝 Registra pagamento", callback_data="fv_register_payment"),
                InlineKeyboardButton("📊 Report annuale", callback_data="fv_annual_report")
            ],
            [
                InlineKeyboardButton("🔍 Cerca FV", callback_data="fv_search"),
                InlineKeyboardButton("📤 Esporta lista", callback_data="fv_export")
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

async def travel_sheet_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle travel sheet callbacks"""
    query = update.callback_query
    action = query.data.replace("fv_", "")
    
    if action == "register_payment":
        await ask_payment_details(update, context)
    elif action == "annual_report":
        await show_annual_report(update, context)
    elif action == "search":
        await search_travel_sheet(update, context)
    elif action == "export":
        await export_travel_sheets(update, context)

async def register_payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Register travel sheet payment"""
    await ask_payment_details(update, context)

async def ask_payment_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask which travel sheets were paid"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get unpaid sheets
        unpaid_sheets = db.query(TravelSheet).filter(
            TravelSheet.user_id == user.id,
            TravelSheet.is_paid == False
        ).order_by(TravelSheet.date).all()
        
        if not unpaid_sheets:
            text = "✅ Non hai fogli viaggio da pagare!"
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text,
                    parse_mode='HTML',
                    reply_markup=get_back_keyboard("back_to_fv")
                )
            else:
                await update.message.reply_text(text, parse_mode='HTML')
            return
        
        text = "💰 <b>REGISTRAZIONE PAGAMENTO FV</b>\\n\\n"
        text += "Seleziona i fogli viaggio pagati:\\n\\n"
        
        # List sheets
        context.user_data['unpaid_sheets'] = {}
        for i, sheet in enumerate(unpaid_sheets):
            text += f"{i+1}. FV {sheet.sheet_number} del {format_date(sheet.date)}\\n"
            text += f"   {sheet.destination} - {format_currency(sheet.amount)}\\n\\n"
            context.user_data['unpaid_sheets'][str(i+1)] = sheet.id
        
        text += "Inserisci i numeri separati da virgola (es: 1,3,5)\\n"
        text += "oppure 'tutti' per selezionare tutti:"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, parse_mode='HTML')
        else:
            await update.message.reply_text(text, parse_mode='HTML')
        
        context.user_data['waiting_for_fv_selection'] = True
        
    finally:
        db.close()

async def show_annual_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show annual travel sheet report"""
    user_id = str(update.effective_user.id)
    current_year = datetime.now().year
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get yearly data
        yearly_sheets = db.query(TravelSheet).filter(
            TravelSheet.user_id == user.id,
            extract('year', TravelSheet.date) == current_year
        ).all()
        
        text = f"📊 <b>REPORT FOGLI VIAGGIO {current_year}</b>\\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\\n\\n"
        
        # Monthly breakdown
        monthly_data = {}
        for sheet in yearly_sheets:
            month = sheet.date.month
            if month not in monthly_data:
                monthly_data[month] = {'count': 0, 'amount': 0, 'paid': 0}
            
            monthly_data[month]['count'] += 1
            monthly_data[month]['amount'] += sheet.amount
            if sheet.is_paid:
                monthly_data[month]['paid'] += sheet.amount
        
        months = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", 
                 "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        
        total_amount = 0
        total_paid = 0
        
        for month in range(1, 13):
            if month in monthly_data:
                data = monthly_data[month]
                total_amount += data['amount']
                total_paid += data['paid']
                
                text += f"<b>{months[month-1]}:</b> {data['count']} FV - "
                text += f"{format_currency(data['amount'])}\\n"
                
                if data['paid'] < data['amount']:
                    pending = data['amount'] - data['paid']
                    text += f"└ ⏳ Da ricevere: {format_currency(pending)}\\n"
        
        text += f"\\n<b>TOTALE ANNO:</b>\\n"
        text += f"├ FV emessi: {len(yearly_sheets)}\\n"
        text += f"├ Importo totale: {format_currency(total_amount)}\\n"
        text += f"├ Già pagato: {format_currency(total_paid)}\\n"
        text += f"└ Da ricevere: {format_currency(total_amount - total_paid)}\\n"
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=get_back_keyboard("back_to_fv")
        )
        
    finally:
        db.close()

async def back_to_fv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to travel sheets dashboard"""
    await travel_sheets_command(update, context)

async def search_travel_sheet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for specific travel sheet"""
    await update.callback_query.answer()
    
    text = "🔍 <b>RICERCA FOGLIO VIAGGIO</b>\\n\\n"
    text += "Inserisci il numero del foglio viaggio:"
    
    await update.callback_query.edit_message_text(text, parse_mode='HTML')
    
    context.user_data['waiting_for_fv_search'] = True

async def export_travel_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export travel sheets to Excel"""
    await update.callback_query.answer("Funzione in sviluppo", show_alert=True)
'''

# Scrivi il file
with open("handlers/travel_sheet_handler.py", "w") as f:
    f.write(handler_content)

print("✅ File handlers/travel_sheet_handler.py creato!")
print("\nProssimi passi:")
print("1. python3 git_update.py")
print("2. Scegli 'feat' e inserisci 'aggiunto travel sheet handler mancante'")
