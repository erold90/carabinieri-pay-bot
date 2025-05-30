"""
Settings handler
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime

from database.connection import SessionLocal
from database.models import User
from config.constants import RANKS
from utils.keyboards import get_rank_keyboard, get_irpef_keyboard, get_back_keyboard
from utils.formatters import format_currency

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings menu"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        text = "⚙️ <b>CONFIGURAZIONE AVANZATA</b>\n\n"
        
        # Personal data
        text += "👤 <b>DATI PERSONALI</b>\n"
        text += f"├ Grado: {user.rank or 'Da configurare'} ▼\n"
        text += f"├ Parametro: {user.parameter}\n"
        text += f"├ Aliquota IRPEF: {int(user.irpef_rate * 100)}% ▼\n"
        text += f"├ Turno base: {user.base_shift_hours} ore\n"
        text += f"├ Anzianità: {user.years_of_service} anni\n"
        text += f"└ Comando: {user.command or 'Da configurare'}\n\n"
        
        # Leave management
        text += "🏖️ <b>GESTIONE LICENZE</b>\n"
        text += f"├ Licenza {datetime.now().year} totale: {user.current_year_leave}gg\n"
        text += f"├ Licenza {datetime.now().year} residua: {user.current_year_leave - user.current_year_leave_used}gg ✏️\n"
        text += f"├ Licenza {datetime.now().year - 1} residua: {user.previous_year_leave}gg ✏️\n"
        text += "└ Calcolo automatico: ✓\n\n"
        
        # Overtime management
        text += "⏰ <b>GESTIONE STRAORDINARI</b>\n"
        text += "├ Limite mensile pagato: 55h\n"
        text += "├ Pagamento eccedenze: Giugno/Dicembre\n"
        text += "├ Tracciamento per tipo: ✓\n"
        text += "└ Report accumulo: Mensile\n\n"
        
        # Travel sheets
        text += "📋 <b>GESTIONE FOGLI VIAGGIO</b>\n"
        text += "├ Alert pagamento: 90gg ✓\n"
        text += "├ Cadenza media: 4-5 mesi\n"
        text += "└ Tracciamento automatico: ✓\n\n"
        
        # Location and routes
        text += "📍 <b>SEDE E PERCORSI</b>\n"
        text += f"├ Comando: {user.command or 'Da configurare'}\n"
        
        if user.patron_saint_date:
            text += f"├ Santo Patrono: {user.patron_saint_date.strftime('%d %B')} ✓\n"
        else:
            text += "├ Santo Patrono: Da configurare\n"
        
        saved_routes = user.saved_routes or {}
        text += f"├ Percorsi salvati: {len(saved_routes)}\n"
        
        if saved_routes:
            for dest, km in list(saved_routes.items())[:3]:
                text += f"│ ├ {dest}: {km}km\n"
            if len(saved_routes) > 3:
                text += f"│ └ ...e altri {len(saved_routes) - 3}\n"
        
        text += "└ Tariffa km: €0,35\n\n"
        
        # Notifications
        text += "🔔 <b>NOTIFICHE INTELLIGENTI</b>\n"
        notifications = user.notification_settings or {}
        text += f"☑️ Promemoria serale: {'✓' if notifications.get('evening_reminder', True) else '✗'}\n"
        text += f"☑️ Alert turni >12h: {'✓' if notifications.get('double_shift_alert', True) else '✗'}\n"
        text += f"☑️ Scadenza licenze: {'✓' if notifications.get('leave_expiry', True) else '✗'}\n"
        
        # Keyboard
        keyboard = [
            [
                InlineKeyboardButton("👤 Dati personali", callback_data="settings_personal"),
                InlineKeyboardButton("🏖️ Licenze", callback_data="settings_leaves")
            ],
            [
                InlineKeyboardButton("📍 Sede e percorsi", callback_data="settings_location"),
                InlineKeyboardButton("🔔 Notifiche", callback_data="settings_notifications")
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

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle settings callbacks"""
    query = update.callback_query
    action = query.data.replace("settings_", "")
    
    if action == "personal":
        await show_personal_settings(update, context)
    elif action == "leaves":
        await show_leave_settings(update, context)
    elif action == "location":
        await show_location_settings(update, context)
    elif action == "notifications":
        await show_notification_settings(update, context)
    elif action.startswith("rank_"):
        await update_rank(update, context)
    elif action.startswith("irpef_"):
        await update_irpef(update, context)
    elif action == "command":
        await ask_command(update, context)
    elif action == "base_hours":
        await ask_base_hours(update, context)

async def show_personal_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show personal data settings"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        text = "👤 <b>DATI PERSONALI</b>\n\n"
        text += f"Grado attuale: <b>{user.rank or 'Non impostato'}</b>\n"
        text += f"Parametro: <b>{user.parameter}</b>\n"
        text += f"Aliquota IRPEF: <b>{int(user.irpef_rate * 100)}%</b>\n"
        text += f"Turno base: <b>{user.base_shift_hours} ore</b>\n"
        text += f"Comando: <b>{user.command or 'Non impostato'}</b>\n\n"
        text += "Seleziona cosa modificare:"
        
        keyboard = [
            [InlineKeyboardButton("🎖️ Modifica grado", callback_data="settings_change_rank")],
            [InlineKeyboardButton("💰 Modifica IRPEF", callback_data="settings_change_irpef")],
            [InlineKeyboardButton("⏰ Modifica turno base", callback_data="settings_base_hours")],
            [InlineKeyboardButton("🏛️ Modifica comando", callback_data="settings_command")],
            [InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    finally:
        db.close()

async def show_leave_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leave settings"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        current_year = datetime.now().year
        
        text = "🏖️ <b>GESTIONE LICENZE</b>\n\n"
        text += f"<b>Licenza {current_year}:</b>\n"
        text += f"├ Giorni totali: {user.current_year_leave}\n"
        text += f"├ Utilizzati: {user.current_year_leave_used}\n"
        text += f"└ Residui: {user.current_year_leave - user.current_year_leave_used}\n\n"
        
        text += f"<b>Licenza {current_year - 1}:</b>\n"
        text += f"└ Giorni residui: {user.previous_year_leave}\n\n"
        
        text += "Inserisci il numero di giorni da modificare:"
        
        keyboard = [
            [InlineKeyboardButton(f"📅 Licenze {current_year}", callback_data="settings_current_leave")],
            [InlineKeyboardButton(f"📅 Licenze {current_year - 1}", callback_data="settings_previous_leave")],
            [InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    finally:
        db.close()

async def show_location_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show location and route settings"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        text = "📍 <b>SEDE E PERCORSI</b>\n\n"
        text += f"Comando: <b>{user.command or 'Non impostato'}</b>\n"
        
        if user.patron_saint_date:
            text += f"Santo Patrono: <b>{user.patron_saint_date.strftime('%d %B')}</b>\n"
        else:
            text += "Santo Patrono: <b>Non impostato</b>\n"
        
        text += "\n<b>PERCORSI SALVATI:</b>\n"
        
        saved_routes = user.saved_routes or {}
        if saved_routes:
            for dest, km in saved_routes.items():
                text += f"├ {dest}: {km}km\n"
        else:
            text += "Nessun percorso salvato\n"
        
        keyboard = [
            [InlineKeyboardButton("🏛️ Modifica comando", callback_data="settings_command")],
            [InlineKeyboardButton("📅 Imposta Santo Patrono", callback_data="settings_patron")],
            [InlineKeyboardButton("➕ Aggiungi percorso", callback_data="settings_add_route")],
            [InlineKeyboardButton("➖ Rimuovi percorso", callback_data="settings_remove_route")],
            [InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    finally:
        db.close()

async def show_notification_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show notification settings"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        notifications = user.notification_settings or {
            'evening_reminder': True,
            'double_shift_alert': True,
            'super_holiday_alert': True,
            'weekly_report': True,
            'overtime_limit': True,
            'leave_expiry': True,
            'travel_sheet_alert': True
        }
        
        text = "🔔 <b>NOTIFICHE INTELLIGENTI</b>\n\n"
        text += "Seleziona quali notifiche ricevere:\n\n"
        
        keyboard = []
        
        notification_names = {
            'evening_reminder': 'Promemoria serale',
            'double_shift_alert': 'Alert turni >12h',
            'super_holiday_alert': 'Avviso super-festivi',
            'weekly_report': 'Report settimanale',
            'overtime_limit': 'Limite straordinari',
            'leave_expiry': 'Scadenza licenze',
            'travel_sheet_alert': 'FV in attesa >90gg'
        }
        
        for key, name in notification_names.items():
            status = "✅" if notifications.get(key, True) else "❌"
            keyboard.append([InlineKeyboardButton(
                f"{status} {name}",
                callback_data=f"settings_toggle_{key}"
            )])
        
        keyboard.append([InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_settings")])
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    finally:
        db.close()

async def update_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update user rank"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "settings_change_rank":
        text = "🎖️ <b>SELEZIONA IL TUO GRADO</b>\n\n"
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=get_rank_keyboard()
        )
    else:
        # Save selected rank
        rank_index = int(query.data.replace("rank_", ""))
        selected_rank = RANKS[rank_index]
        
        user_id = str(query.from_user.id)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            user.rank = selected_rank
            
            # Update parameter based on rank
            # TODO: Add parameter table
            
            db.commit()
            
            await query.edit_message_text(
                f"✅ Grado aggiornato: <b>{selected_rank}</b>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Torna alle impostazioni", callback_data="back_to_settings")]
                ])
            )
            
        finally:
            db.close()

async def update_irpef(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update IRPEF rate"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "settings_change_irpef":
        text = "💰 <b>SELEZIONA L'ALIQUOTA IRPEF</b>\n\n"
        text += "Seleziona la tua aliquota IRPEF attuale:"
        
        await query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=get_irpef_keyboard()
        )
    else:
        # Save selected rate
        rate = int(query.data.replace("irpef_", ""))
        
        user_id = str(query.from_user.id)
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            user.irpef_rate = rate / 100
            db.commit()
            
            await query.edit_message_text(
                f"✅ Aliquota IRPEF aggiornata: <b>{rate}%</b>",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Torna alle impostazioni", callback_data="back_to_settings")]
                ])
            )
            
        finally:
            db.close()

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for command name"""
    await update.callback_query.answer()
    
    text = "🏛️ <b>INSERISCI IL TUO COMANDO</b>\n\n"
    text += "Scrivi il nome del comando di appartenenza:"
    
    await update.callback_query.edit_message_text(text, parse_mode='HTML')
    
    context.user_data['waiting_for_command'] = True

async def ask_base_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for base shift hours"""
    await update.callback_query.answer()
    
    text = "⏰ <b>ORE TURNO BASE</b>\n\n"
    text += "Inserisci il numero di ore del tuo turno base (normalmente 6):"
    
    await update.callback_query.edit_message_text(text, parse_mode='HTML')
    
    context.user_data['waiting_for_base_hours'] = True

async def show_rank_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show rank selection keyboard"""
    await update_rank(update, context)

async def show_irpef_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show IRPEF selection keyboard"""
    await update_irpef(update, context)

async def handle_settings_personal_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle personal settings modification callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "settings_change_rank":
        await update_rank(update, context)
    elif data == "settings_change_irpef":
        await update_irpef(update, context)
    elif data == "settings_base_hours":
        await ask_base_hours(update, context)
    elif data == "settings_command":
        await ask_command(update, context)
    elif data == "back_to_settings":
        await settings_command(update, context)
