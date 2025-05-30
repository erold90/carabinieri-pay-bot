"""
Settings handler completo con verifica database
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
        
        if not user:
            await update.effective_message.reply_text(
                "❌ Utente non trovato. Usa /start per registrarti."
            )
            return
        
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
    """Handle all settings callbacks"""
    query = update.callback_query
    await query.answer()
    
    action = query.data.replace("settings_", "")
    
    # Routing to specific functions
    if action == "personal":
        await show_personal_settings(update, context)
    elif action == "leaves":
        await show_leave_settings(update, context)
    elif action == "location":
        await show_location_settings(update, context)
    elif action == "notifications":
        await show_notification_settings(update, context)
    elif action == "change_rank":
        await show_rank_selection(update, context)
    elif action == "change_irpef":
        await show_irpef_selection(update, context)
    elif action == "command":
        await ask_command(update, context)
    elif action == "base_hours":
        await ask_base_hours(update, context)
    elif action.startswith("toggle_"):
        await toggle_notification(update, context)

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

async def show_rank_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show rank selection"""
    text = "🎖️ <b>SELEZIONA IL TUO GRADO</b>\n\n"
    
    await update.callback_query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=get_rank_keyboard()
    )

async def show_irpef_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show IRPEF selection with guide"""
    text = "💰 <b>SELEZIONA L'ALIQUOTA IRPEF</b>\n\n"
    text += "📊 <b>GUIDA SCAGLIONI IRPEF 2024:</b>\n"
    text += "• Fino a €15.000 di reddito: <b>23%</b>\n"
    text += "• Da €15.001 a €28.000: <b>25%</b>\n"
    text += "• Da €28.001 a €50.000: <b>35%</b>\n"
    text += "• Oltre €50.000: <b>43%</b>\n\n"
    text += "💡 <i>Puoi verificare la tua aliquota sul cedolino stipendio</i>\n\n"
    text += "Seleziona la tua aliquota attuale:"
    
    await update.callback_query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=get_irpef_keyboard()
    )


async def update_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update user rank with DB verification"""
    query = update.callback_query
    await query.answer()
    
    rank_index = int(query.data.replace("rank_", ""))
    selected_rank = RANKS[rank_index]
    
    user_id = str(query.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        user.rank = selected_rank
        
        # Update parameter based on rank (esempio di parametri)
        rank_parameters = {
            'Carabiniere': 101.25,
            'Carabiniere Scelto': 102.5,
            'Appuntato': 104.0,
            'Appuntato Scelto QS': 106.5,
            'Vice Brigadiere': 108.5,
            'Brigadiere': 110.0,
            'Brigadiere CA QS': 112.5,
            'Maresciallo': 115.0,
            'Maresciallo Ordinario': 117.5,
            'Maresciallo Capo': 120.0,
            'Maresciallo Aiutante': 122.5,
            'Maresciallo Aiutante QS': 125.0,
            'Luogotenente': 127.5,
            'Luogotenente QS': 130.0,
        }
        
        if selected_rank in rank_parameters:
            user.parameter = rank_parameters[selected_rank]
        
        db.commit()
        
        # Verifica che sia stato salvato
        db.refresh(user)
        if user.rank == selected_rank:
            await query.edit_message_text(
                f"✅ Grado aggiornato: <b>{selected_rank}</b>\n"
                f"Parametro: <b>{user.parameter}</b>\n\n"
                "✅ Modifiche salvate nel database!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Torna alle impostazioni", callback_data="settings_personal")]
                ])
            )
        else:
            await query.edit_message_text(
                "❌ Errore nel salvataggio. Riprova.",
                parse_mode='HTML'
            )
        
    except Exception as e:
        print(f"[ERROR] Aggiornamento grado: {e}")
        await query.edit_message_text(
            "❌ Errore nel database. Riprova più tardi.",
            parse_mode='HTML'
        )
    finally:
        db.close()

async def update_irpef(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Update IRPEF rate with DB verification"""
    query = update.callback_query
    await query.answer()
    
    rate = int(query.data.replace("irpef_", ""))
    
    user_id = str(query.from_user.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        user.irpef_rate = rate / 100
        db.commit()
        
        # Verifica
        db.refresh(user)
        if user.irpef_rate == rate / 100:
            await query.edit_message_text(
                f"✅ Aliquota IRPEF aggiornata: <b>{rate}%</b>\n\n"
                "✅ Modifiche salvate nel database!",
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ Torna alle impostazioni", callback_data="settings_personal")]
                ])
            )
        else:
            await query.edit_message_text(
                "❌ Errore nel salvataggio. Riprova.",
                parse_mode='HTML'
            )
        
    except Exception as e:
        print(f"[ERROR] Aggiornamento IRPEF: {e}")
        await query.edit_message_text(
            "❌ Errore nel database. Riprova più tardi.",
            parse_mode='HTML'
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
    context.user_data['settings_message_id'] = update.callback_query.message.message_id

async def ask_base_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for base shift hours"""
    await update.callback_query.answer()
    
    text = "⏰ <b>ORE TURNO BASE</b>\n\n"
    text += "Inserisci il numero di ore del tuo turno base (normalmente 6):"
    
    await update.callback_query.edit_message_text(text, parse_mode='HTML')
    
    context.user_data['waiting_for_base_hours'] = True
    context.user_data['settings_message_id'] = update.callback_query.message.message_id

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for settings"""
    user_id = str(update.effective_user.id)
    
    if context.user_data.get('waiting_for_command'):
        command_name = update.message.text.strip()
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.telegram_id == user_id).first()
            user.command = command_name
            db.commit()
            
            # Verifica
            db.refresh(user)
            if user.command == command_name:
                await update.message.reply_text(
                    f"✅ Comando aggiornato: <b>{command_name}</b>\n\n"
                    "✅ Modifiche salvate nel database!",
                    parse_mode='HTML',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("⬅️ Torna alle impostazioni", callback_data="settings_personal")]
                    ])
                )
            else:
                await update.message.reply_text(
                    "❌ Errore nel salvataggio. Riprova.",
                    parse_mode='HTML'
                )
            
            context.user_data['waiting_for_command'] = False
            
        except Exception as e:
            print(f"[ERROR] Aggiornamento comando: {e}")
            await update.message.reply_text(
                "❌ Errore nel database. Riprova più tardi.",
                parse_mode='HTML'
            )
        finally:
            db.close()
            
    elif context.user_data.get('waiting_for_base_hours'):
        try:
            hours = int(update.message.text.strip())
            if 1 <= hours <= 24:
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.telegram_id == user_id).first()
                    user.base_shift_hours = hours
                    db.commit()
                    
                    # Verifica
                    db.refresh(user)
                    if user.base_shift_hours == hours:
                        await update.message.reply_text(
                            f"✅ Turno base aggiornato: <b>{hours} ore</b>\n\n"
                            "✅ Modifiche salvate nel database!",
                            parse_mode='HTML',
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton("⬅️ Torna alle impostazioni", callback_data="settings_personal")]
                            ])
                        )
                    else:
                        await update.message.reply_text(
                            "❌ Errore nel salvataggio. Riprova.",
                            parse_mode='HTML'
                        )
                    
                    context.user_data['waiting_for_base_hours'] = False
                    
                except Exception as e:
                    print(f"[ERROR] Aggiornamento ore base: {e}")
                    await update.message.reply_text(
                        "❌ Errore nel database. Riprova più tardi.",
                        parse_mode='HTML'
                    )
                finally:
                    db.close()
            else:
                await update.message.reply_text("❌ Inserisci un numero tra 1 e 24")
        except ValueError:
            await update.message.reply_text("❌ Inserisci un numero valido")


async def show_leave_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show leave settings"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        text = "🏖️ <b>CONFIGURAZIONE LICENZE</b>\n\n"
        text += f"📅 <b>Anno {datetime.now().year}:</b>\n"
        text += f"├ Giorni totali spettanti: {user.current_year_leave}\n"
        text += f"├ Giorni utilizzati: {user.current_year_leave_used}\n"
        text += f"└ Giorni residui: {user.current_year_leave - user.current_year_leave_used}\n\n"
        
        text += f"📅 <b>Anno {datetime.now().year - 1}:</b>\n"
        text += f"├ Giorni riportati: {user.previous_year_leave}\n"
        text += f"└ Scadenza: 31/03/{datetime.now().year}\n\n"
        
        text += "Modifica i valori:"
        
        keyboard = [
            [InlineKeyboardButton(f"✏️ Licenza {datetime.now().year} totale", callback_data="edit_current_leave_total")],
            [InlineKeyboardButton(f"✏️ Licenza {datetime.now().year} utilizzata", callback_data="edit_current_leave_used")],
            [InlineKeyboardButton(f"✏️ Licenza {datetime.now().year - 1} residua", callback_data="edit_previous_leave")],
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
    """Show location settings"""
    user_id = str(update.effective_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        text = "📍 <b>SEDE E PERCORSI SALVATI</b>\n\n"
        
        # Percorsi salvati
        saved_routes = user.saved_routes or {}
        if saved_routes:
            text += "🚗 <b>Percorsi frequenti:</b>\n"
            for name, details in saved_routes.items():
                text += f"├ {name}: {details.get('km', 0)} km\n"
            text += "\n"
        else:
            text += "Nessun percorso salvato\n\n"
        
        text += "📌 <b>Sede di servizio:</b>\n"
        text += f"{user.command or 'Non configurato'}\n\n"
        
        text += "🗓️ <b>Santo Patrono:</b>\n"
        if user.patron_saint_date:
            text += f"{user.patron_saint_date.strftime('%d/%m')}\n"
        else:
            text += "Non configurato\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ Aggiungi percorso", callback_data="add_route")],
            [InlineKeyboardButton("📅 Imposta Santo Patrono", callback_data="set_patron_saint")],
            [InlineKeyboardButton("🗑️ Rimuovi percorso", callback_data="remove_route")],
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
        
        # Impostazioni notifiche (default se non esistono)
        notifications = user.notification_settings or {
            'daily_reminder': False,
            'overtime_limit': True,
            'leave_expiry': True,
            'travel_sheet_reminder': True,
            'reminder_time': '09:00'
        }
        
        text = "🔔 <b>IMPOSTAZIONI NOTIFICHE</b>\n\n"
        
        # Stato attuale
        text += "📱 <b>Notifiche attive:</b>\n"
        text += f"├ Promemoria giornaliero: {'✅' if notifications.get('daily_reminder') else '❌'}\n"
        text += f"├ Avviso limite straordinari: {'✅' if notifications.get('overtime_limit') else '❌'}\n"
        text += f"├ Scadenza licenze: {'✅' if notifications.get('leave_expiry') else '❌'}\n"
        text += f"└ Promemoria fogli viaggio: {'✅' if notifications.get('travel_sheet_reminder') else '❌'}\n\n"
        
        text += f"⏰ Orario notifiche: {notifications.get('reminder_time', '09:00')}\n"
        
        keyboard = [
            [InlineKeyboardButton(
                f"{'🔕' if notifications.get('daily_reminder') else '🔔'} Promemoria giornaliero",
                callback_data="toggle_daily_reminder"
            )],
            [InlineKeyboardButton(
                f"{'🔕' if notifications.get('overtime_limit') else '🔔'} Avviso straordinari",
                callback_data="toggle_overtime_limit"
            )],
            [InlineKeyboardButton(
                f"{'🔕' if notifications.get('leave_expiry') else '🔔'} Scadenza licenze",
                callback_data="toggle_leave_expiry"
            )],
            [InlineKeyboardButton(
                f"{'🔕' if notifications.get('travel_sheet_reminder') else '🔔'} Promemoria FV",
                callback_data="toggle_travel_sheet"
            )],
            [InlineKeyboardButton("⏰ Cambia orario", callback_data="change_reminder_time")],
            [InlineKeyboardButton("⬅️ Indietro", callback_data="back_to_settings")]
        ]
        
        await update.callback_query.edit_message_text(
            text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
    finally:
        db.close()

async def toggle_notification(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle notification setting"""
    query = update.callback_query
    await query.answer()
    
    setting = query.data.replace("toggle_", "")
    user_id = str(query.from_user.id)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Get current settings
        notifications = user.notification_settings or {
            'daily_reminder': False,
            'overtime_limit': True,
            'leave_expiry': True,
            'travel_sheet_reminder': True,
            'reminder_time': '09:00'
        }
        
        # Map callback to setting key
        setting_map = {
            'daily_reminder': 'daily_reminder',
            'overtime_limit': 'overtime_limit',
            'leave_expiry': 'leave_expiry',
            'travel_sheet': 'travel_sheet_reminder'
        }
        
        if setting in setting_map:
            key = setting_map[setting]
            notifications[key] = not notifications.get(key, False)
            
            # Save
            user.notification_settings = notifications
            db.commit()
            
            await query.answer(f"{'Attivato' if notifications[key] else 'Disattivato'}!")
            
            # Refresh view
            await show_notification_settings(update, context)
        
    finally:
        db.close()


# Handlers di supporto per settings
async def handle_leave_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle leave editing"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    text = "✏️ Inserisci il nuovo valore:"
    
    if "current_leave_total" in action:
        text = "✏️ Giorni totali di licenza per l'anno corrente:"
    elif "current_leave_used" in action:
        text = "✏️ Giorni di licenza già utilizzati:"
    elif "previous_leave" in action:
        text = "✏️ Giorni residui dall'anno precedente:"
    
    await query.edit_message_text(text, parse_mode='HTML')
    context.user_data['editing_leave'] = action
    context.user_data['waiting_for_leave_value'] = True

async def handle_route_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle route add/remove"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "add_route":
        await query.edit_message_text(
            "📍 <b>AGGIUNGI PERCORSO</b>\n\n"
            "Inserisci il nome del percorso (es: Casa-Caserma):",
            parse_mode='HTML'
        )
        context.user_data['adding_route'] = True
    else:
        await query.edit_message_text(
            "🗑️ Funzione in sviluppo",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ Indietro", callback_data="settings_location")]
            ])
        )

async def handle_patron_saint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle patron saint date setting"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📅 <b>SANTO PATRONO</b>\n\n"
        "Inserisci la data (formato GG/MM):\n"
        "Esempio: 29/09 per San Michele",
        parse_mode='HTML'
    )
    context.user_data['setting_patron_saint'] = True

async def handle_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle reminder time change"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "⏰ <b>ORARIO NOTIFICHE</b>\n\n"
        "Inserisci l'orario (formato HH:MM):\n"
        "Esempio: 09:00",
        parse_mode='HTML'
    )
    context.user_data['setting_reminder_time'] = True
