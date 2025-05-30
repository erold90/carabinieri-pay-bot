"""
Travel sheet management handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime, date
from sqlalchemy import extract, func

from database.connection import SessionLocal
from database.models import User, TravelSheet
from config.settings import get_current_date, SELECT_TRAVEL_SHEETS, PAYMENT_DETAILS
from utils.formatters import format_currency, format_date, format_month_year
from utils.keyboards import get_back_keyboard

async def travel_sheets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show travel sheets dashboard"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get unpaid travel sheets
        unpaid_sheets = db.query(TravelSheet).filter(
            TravelSheet.user_id == user.id,
            TravelSheet.is_paid == False
        ).order_by(TravelSheet.date).all()
        
        # Get last payment
        last_payment = db.query(TravelSheet).filter(
            TravelSheet.user_id == user.id,
            TravelSheet.is_paid == True
        ).order_by(TravelSheet.paid_date.desc()).first()
        
        # Group by month
        sheets_by_month = {}
        total_amount = 0
        
        for sheet in unpaid_sheets:
            month_key = sheet.date.strftime("%Y-%m")
            if month_key not in sheets_by_month:
                sheets_by_month[month_key] = {
                    'sheets': [],
                    'amount': 0,
                    'count': 0
                }
            
            sheets_by_month[month_key]['sheets'].append(sheet)
            sheets_by_month[month_key]['amount'] += sheet.amount
            sheets_by_month[month_key]['count'] += 1
            total_amount += sheet.amount
        
        # Format message
        text = "📋 <b>FOGLI VIAGGIO IN ATTESA PAGAMENTO</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📊 <b>RIEPILOGO GENERALE:</b>\n"
        text += f"├ FV in attesa: {len(unpaid_sheets)} fogli\n"
        text += f"├ Importo totale: {format_currency(total_amount)}\n"
        
        if unpaid_sheets:
            oldest = unpaid_sheets[0]
            text += f"├ FV più vecchio: {oldest.sheet_number} ({format_month_year(oldest.date).upper()})\n"
        
        if last_payment:
            months_ago = (datetime.now().date() - last_payment.paid_date).days // 30
            text += f"├ Ultimo pagamento: {format_month_year(last_payment.paid_date)} ({months_ago} mesi fa)\n"
        else:
            text += "├ Ultimo pagamento: Mai\n"
        
        wait_months = len(sheets_by_month) if sheets_by_month else 0
        text += f"└ ⚠️ Attesa media: {wait_months} mesi\n\n"
        
        if sheets_by_month:
            text += "📑 <b>DETTAGLIO FOGLI VIAGGIO:</b>\n\n"
            
            for month_key in sorted(sheets_by_month.keys()):
                data = sheets_by_month[month_key]
                year, month = month_key.split('-')
                month_date = date(int(year), int(month), 1)
                
                text += f"<b>{format_month_year(month_date).upper()} ({format_currency(data['amount'])})</b>\n"
                
                for sheet in data['sheets'][:3]:  # Show max 3 per month
                    text += f"├ FV {sheet.sheet_number} - {sheet.destination} - "
                    text += f"{format_currency(sheet.amount)}\n"
                
                if data['count'] > 3:
                    text += f"└ ...e altri {data['count'] - 3} fogli\n"
                else:
                    text += "\n"
        else:
            text += "✅ <b>Nessun foglio viaggio in attesa!</b>\n"
        
        # Keyboard
        keyboard = [
            [
                InlineKeyboardButton("💰 Registra pagamento", callback_data="fv_register_payment"),
                InlineKeyboardButton("📊 Export lista", callback_data="fv_export")
            ],
            [
                InlineKeyboardButton("📅 Storico pagamenti", callback_data="fv_history"),
                InlineKeyboardButton("📈 Statistiche", callback_data="fv_stats")
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
        await start_payment_registration(update, context)
    elif action == "export":
        await export_travel_sheets(update, context)
    elif action == "history":
        await show_payment_history(update, context)
    elif action == "stats":
        await show_travel_stats(update, context)
    elif action.startswith("select_"):
        await handle_sheet_selection(update, context)
    elif action == "confirm_payment":
        await confirm_payment(update, context)

async def register_payment_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start payment registration"""
    await start_payment_registration(update, context)

async def start_payment_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the payment registration process"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get unpaid sheets grouped by month
        unpaid_sheets = db.query(TravelSheet).filter(
            TravelSheet.user_id == user.id,
            TravelSheet.is_paid == False
        ).order_by(TravelSheet.date).all()
        
        if not unpaid_sheets:
            text = "✅ Non hai fogli viaggio in attesa di pagamento!"
            
            if update.callback_query:
                await update.callback_query.edit_message_text(
                    text,
                    parse_mode='HTML',
                    reply_markup=get_back_keyboard("back_to_fv")
                )
            else:
                await update.message.reply_text(text, parse_mode='HTML')
            return
        
        # Store sheets in context
        context.user_data['unpaid_sheets'] = unpaid_sheets
        context.user_data['selected_sheets'] = []
        
        text = "💰 <b>REGISTRAZIONE PAGAMENTO FOGLI VIAGGIO</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"Data pagamento: {format_date(get_current_date())}\n\n"
        text += "✅ <b>SELEZIONA I FOGLI PAGATI:</b>\n"
        text += "(puoi selezionare più fogli)\n\n"
        
        # Create selection keyboard
        keyboard = []
        
        # Select all button
        total_amount = sum(sheet.amount for sheet in unpaid_sheets)
        keyboard.append([
            InlineKeyboardButton(
                f"☐ Seleziona tutti ({len(unpaid_sheets)} FV - {format_currency(total_amount)})",
                callback_data="fv_select_all"
            )
        ])
        
        # Group by month
        current_month = None
        month_sheets = []
        
        for i, sheet in enumerate(unpaid_sheets):
            month_key = sheet.date.strftime("%B %Y").upper()
            
            if month_key != current_month:
                if current_month and month_sheets:
                    # Add month header
                    keyboard.append([InlineKeyboardButton(
                        f"━━━ {current_month} ━━━",
                        callback_data="fv_noop"
                    )])
                
                current_month = month_key
                month_sheets = []
            
            # Add sheet button
            check = "☑️" if i in context.user_data.get('selected_sheets', []) else "☐"
            button_text = f"{check} FV {sheet.sheet_number} - {sheet.destination} - {format_currency(sheet.amount)}"
            
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"fv_select_{i}"
            )])
            
            month_sheets.append(i)
        
        # Add last month header if needed
        if current_month and month_sheets:
            keyboard.insert(-len(month_sheets), [InlineKeyboardButton(
                f"━━━ {current_month} ━━━",
                callback_data="fv_noop"
            )])
        
        # Add confirm button
        keyboard.append([
            InlineKeyboardButton("✅ Conferma selezione", callback_data="fv_confirm_selection"),
            InlineKeyboardButton("❌ Annulla", callback_data="back_to_fv")
        ])
        
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
    
    return SELECT_TRAVEL_SHEETS

async def handle_sheet_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle individual sheet selection"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.replace("fv_select_", "")
    
    if action == "all":
        # Toggle all selection
        unpaid_sheets = context.user_data.get('unpaid_sheets', [])
        current_selected = context.user_data.get('selected_sheets', [])
        
        if len(current_selected) == len(unpaid_sheets):
            # Deselect all
            context.user_data['selected_sheets'] = []
        else:
            # Select all
            context.user_data['selected_sheets'] = list(range(len(unpaid_sheets)))
    else:
        # Toggle individual selection
        sheet_index = int(action)
        selected = context.user_data.get('selected_sheets', [])
        
        if sheet_index in selected:
            selected.remove(sheet_index)
        else:
            selected.append(sheet_index)
        
        context.user_data['selected_sheets'] = selected
    
    # Refresh the selection screen
    await start_payment_registration(update, context)

async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and save payment"""
    query = update.callback_query
    
    if query.data == "fv_confirm_selection":
        # Show summary
        selected_indices = context.user_data.get('selected_sheets', [])
        unpaid_sheets = context.user_data.get('unpaid_sheets', [])
        
        if not selected_indices:
            await query.answer("Seleziona almeno un foglio viaggio!", show_alert=True)
            return
        
        selected_sheets = [unpaid_sheets[i] for i in selected_indices]
        total_amount = sum(sheet.amount for sheet in selected_sheets)
        
        # Group by period
        min_date = min(sheet.date for sheet in selected_sheets)
        max_date = max(sheet.date for sheet in selected_sheets)
        
        text = "📊 <b>RIEPILOGO SELEZIONE:</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        text += f"├ Fogli selezionati: {len(selected_sheets)}/{len(unpaid_sheets)}\n"
        text += f"├ Importo totale: {format_currency(total_amount)}\n"
        text += f"├ Periodo: {format_month_year(min_date)} - {format_month_year(max_date)}\n"
        
        remaining = len(unpaid_sheets) - len(selected_sheets)
        if remaining > 0:
            remaining_amount = sum(
                sheet.amount for i, sheet in enumerate(unpaid_sheets) 
                if i not in selected_indices
            )
            text += f"└ FV non selezionati: {remaining} ({format_currency(remaining_amount)})\n"
        
        text += "\n<b>Confermi il pagamento?</b>"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Sì, conferma", callback_data="fv_save_payment"),
                InlineKeyboardButton("📝 Modifica", callback_data="fv_register_payment")
            ]
        ]
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "fv_save_payment":
        # Save payment
        await query.answer("Salvataggio in corso...")
        
        user_id = str(query.from_user.id)
        selected_indices = context.user_data.get('selected_sheets', [])
        unpaid_sheets = context.user_data.get('unpaid_sheets', [])
        selected_sheets = [unpaid_sheets[i] for i in selected_indices]
        
        db = SessionLocal()
        try:
            # Update sheets as paid
            current_date = get_current_date()
            for sheet in selected_sheets:
                db_sheet = db.query(TravelSheet).filter(
                    TravelSheet.id == sheet.id
                ).first()
                
                if db_sheet:
                    db_sheet.is_paid = True
                    db_sheet.paid_date = current_date
            
            db.commit()
            
            # Get updated stats
            remaining_sheets = db.query(TravelSheet).filter(
                TravelSheet.user_id == sheet.user_id,
                TravelSheet.is_paid == False
            ).all()
            
            remaining_amount = sum(s.amount for s in remaining_sheets)
            
            text = "✅ <b>PAGAMENTO REGISTRATO CON SUCCESSO!</b>\n"
            text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            text += f"📅 Data: {format_date(current_date)}\n"
            text += f"💰 Importo ricevuto: {format_currency(sum(s.amount for s in selected_sheets))}\n"
            text += f"📋 Fogli pagati: {len(selected_sheets)}\n\n"
            
            text += "<b>DETTAGLIO FOGLI ARCHIVIATI:</b>\n"
            for sheet in selected_sheets[:5]:
                text += f"├ FV {sheet.sheet_number} ✓ PAGATO\n"
            
            if len(selected_sheets) > 5:
                text += f"└ ...e altri {len(selected_sheets) - 5} fogli\n"
            
            text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            text += "📊 <b>SITUAZIONE AGGIORNATA:</b>\n"
            text += f"├ FV ancora da pagare: {len(remaining_sheets)}\n"
            text += f"├ Importo residuo: {format_currency(remaining_amount)}\n"
            
            if remaining_sheets:
                oldest = min(remaining_sheets, key=lambda x: x.date)
                text += f"├ FV più vecchio: {format_month_year(oldest.date).upper()}\n"
            
            text += "└ Prossimo pagamento stimato: MAG 2025\n"
            
            keyboard = [
                [
                    InlineKeyboardButton("📋 Vedi FV residui", callback_data="back_to_fv"),
                    InlineKeyboardButton("📊 Storico pagamenti", callback_data="fv_history")
                ]
            ]
            
            await query.edit_message_text(
                text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
            # Clear context
            context.user_data.clear()
            
        finally:
            db.close()

async def show_payment_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payment history"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get paid sheets grouped by payment date
        paid_sheets = db.query(
            TravelSheet.paid_date,
            func.count(TravelSheet.id).label('count'),
            func.sum(TravelSheet.amount).label('total'),
            func.min(TravelSheet.date).label('min_date'),
            func.max(TravelSheet.date).label('max_date')
        ).filter(
            TravelSheet.user_id == user.id,
            TravelSheet.is_paid == True
        ).group_by(
            TravelSheet.paid_date
        ).order_by(
            TravelSheet.paid_date.desc()
        ).all()
        
        text = "📊 <b>STORICO PAGAMENTI FOGLI VIAGGIO</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        current_year = None
        year_total = 0
        year_count = 0
        
        for payment in paid_sheets:
            if payment.paid_date.year != current_year:
                if current_year:
                    text += f"\n<b>{current_year}</b> - Totale: {format_currency(year_total)} ({year_count} FV)\n\n"
                
                current_year = payment.paid_date.year
                year_total = 0
                year_count = 0
            
            text += f"├ {format_date(payment.paid_date)} - {format_currency(payment.total)} ({payment.count} FV)\n"
            text += f"│ Periodo: {format_month_year(payment.min_date)} - {format_month_year(payment.max_date)}\n"
            
            year_total += payment.total
            year_count += payment.count
        
        if current_year:
            text += f"\n<b>{current_year}</b> - Totale: {format_currency(year_total)} ({year_count} FV)\n"
        
        # Calculate statistics
        if paid_sheets:
            total_payments = len(paid_sheets)
            total_amount = sum(p.total for p in paid_sheets)
            total_sheets = sum(p.count for p in paid_sheets)
            avg_amount = total_amount / total_payments
            avg_sheets = total_sheets / total_payments
            
            text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            text += "📈 <b>ANALISI:</b>\n"
            text += f"├ Totale pagamenti: {total_payments}\n"
            text += f"├ Importo totale: {format_currency(total_amount)}\n"
            text += f"├ Media per pagamento: {format_currency(avg_amount)}\n"
            text += f"├ FV medi per pagamento: {avg_sheets:.1f}\n"
            
            # Calculate average wait time
            # TODO: Implement when we have more data
        else:
            text += "\n<i>Nessun pagamento registrato</i>"
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_fv")]
            ])
        )
        
    finally:
        db.close()

async def show_travel_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show travel statistics"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get statistics
        current_year = datetime.now().year
        
        # Total sheets
        total_sheets = db.query(func.count(TravelSheet.id)).filter(
            TravelSheet.user_id == user.id
        ).scalar()
        
        # This year sheets
        year_sheets = db.query(func.count(TravelSheet.id)).filter(
            TravelSheet.user_id == user.id,
            extract('year', TravelSheet.date) == current_year
        ).scalar()
        
        # Paid vs unpaid
        paid_count = db.query(func.count(TravelSheet.id)).filter(
            TravelSheet.user_id == user.id,
            TravelSheet.is_paid == True
        ).scalar()
        
        unpaid_count = total_sheets - paid_count
        
        # Average amounts
        avg_amount = db.query(func.avg(TravelSheet.amount)).filter(
            TravelSheet.user_id == user.id
        ).scalar() or 0
        
        # Most frequent destinations
        top_destinations = db.query(
            TravelSheet.destination,
            func.count(TravelSheet.id).label('count')
        ).filter(
            TravelSheet.user_id == user.id
        ).group_by(
            TravelSheet.destination
        ).order_by(
            func.count(TravelSheet.id).desc()
        ).limit(5).all()
        
        text = "📈 <b>STATISTICHE FOGLI VIAGGIO</b>\n"
        text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📊 <b>RIEPILOGO GENERALE:</b>\n"
        text += f"├ Fogli viaggio totali: {total_sheets}\n"
        text += f"├ Fogli {current_year}: {year_sheets}\n"
        text += f"├ Pagati: {paid_count} ({paid_count/total_sheets*100:.0f}%)\n"
        text += f"├ In attesa: {unpaid_count} ({unpaid_count/total_sheets*100:.0f}%)\n"
        text += f"└ Importo medio: {format_currency(avg_amount)}\n\n"
        
        if top_destinations:
            text += "📍 <b>DESTINAZIONI FREQUENTI:</b>\n"
            for dest, count in top_destinations:
                text += f"├ {dest}: {count} viaggi\n"
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_fv")]
            ])
        )
        
    finally:
        db.close()

async def export_travel_sheets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export travel sheets list"""
    # TODO: Implement Excel export
    await update.callback_query.answer(
        "Funzione export in sviluppo",
        show_alert=True
    )