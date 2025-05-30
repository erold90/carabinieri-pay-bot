"""
Setup handler per configurazione iniziale utente
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from datetime import datetime

from database.connection import SessionLocal
from database.models import User
from config.constants import RANKS
from config.settings import SETUP_RANK, SETUP_COMMAND, SETUP_IRPEF, SETUP_LEAVE
from utils.keyboards import get_rank_keyboard, get_irpef_keyboard

# Stati conversazione setup
SETUP_RANK, SETUP_COMMAND, SETUP_IRPEF, SETUP_LEAVE = range(4)

async def setup_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Inizia il processo di setup"""
   query = update.callback_query
   await query.answer()
   
   text = "🎖️ <b>CONFIGURAZIONE PROFILO</b>\n\n"
   text += "Passo 1 di 4: Seleziona il tuo grado\n\n"
   text += "Questo determinerà il parametro stipendiale base:"
   
   await query.edit_message_text(
       text,
       parse_mode='HTML',
       reply_markup=get_rank_keyboard()
   )
   
   return SETUP_RANK

async def setup_rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Gestisce selezione grado"""
   query = update.callback_query
   await query.answer()
   
   rank_index = int(query.data.replace("rank_", ""))
   selected_rank = RANKS[rank_index]
   
   context.user_data['setup_rank'] = selected_rank
   
   # Parametri stipendiali per grado
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
   
   parameter = rank_parameters.get(selected_rank, 108.5)
   context.user_data['setup_parameter'] = parameter
   
   text = f"✅ Grado selezionato: <b>{selected_rank}</b>\n"
   text += f"📊 Parametro: <b>{parameter}</b>\n\n"
   text += "🏛️ <b>Passo 2 di 4: Comando di appartenenza</b>\n\n"
   text += "Inserisci il nome del tuo comando (es: Stazione CC Roma Parioli):"
   
   await query.edit_message_text(text, parse_mode='HTML')
   
   return SETUP_COMMAND

async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Gestisce inserimento comando"""
   command_name = update.message.text.strip()
   context.user_data['setup_command'] = command_name
   
   text = f"✅ Comando: <b>{command_name}</b>\n\n"
   text += "💰 <b>Passo 3 di 4: Aliquota IRPEF</b>\n\n"
   text += "Seleziona la tua aliquota IRPEF attuale:\n"
   text += "(Puoi verificarla sul cedolino stipendio)"
   
   await update.message.reply_text(
       text,
       parse_mode='HTML',
       reply_markup=get_irpef_keyboard()
   )
   
   return SETUP_IRPEF

async def setup_irpef(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Gestisce selezione IRPEF"""
   query = update.callback_query
   await query.answer()
   
   rate = int(query.data.replace("irpef_", ""))
   context.user_data['setup_irpef'] = rate / 100
   
   current_year = datetime.now().year
   
   text = f"✅ Aliquota IRPEF: <b>{rate}%</b>\n\n"
   text += "🏖️ <b>Passo 4 di 4: Licenze residue</b>\n\n"
   text += f"Quanti giorni di licenza {current_year} hai ancora disponibili?\n"
   text += "(Inserisci un numero, es: 25)"
   
   await query.edit_message_text(text, parse_mode='HTML')
   
   return SETUP_LEAVE

async def setup_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Gestisce inserimento licenze e completa setup"""
   try:
       leave_days = int(update.message.text.strip())
       
       if leave_days < 0 or leave_days > 32:
           await update.message.reply_text(
               "❌ Inserisci un numero valido (0-32)",
               parse_mode='HTML'
           )
           return SETUP_LEAVE
       
       # Salva tutto nel database
       user_id = str(update.effective_user.id)
       db = SessionLocal()
       try:
           user = db.query(User).filter(User.telegram_id == user_id).first()
           
           # Aggiorna tutti i dati
           user.rank = context.user_data['setup_rank']
           user.parameter = context.user_data['setup_parameter']
           user.command = context.user_data['setup_command']
           user.irpef_rate = context.user_data['setup_irpef']
           user.current_year_leave = 32  # Standard annuale
           user.current_year_leave_used = 32 - leave_days
           
           db.commit()
           
           # Messaggio di completamento
           text = "🎉 <b>CONFIGURAZIONE COMPLETATA!</b>\n\n"
           text += "Il tuo profilo è stato configurato:\n\n"
           text += f"🎖️ Grado: <b>{user.rank}</b>\n"
           text += f"🏛️ Comando: <b>{user.command}</b>\n"
           text += f"💰 IRPEF: <b>{int(user.irpef_rate * 100)}%</b>\n"
           text += f"🏖️ Licenze residue: <b>{leave_days} giorni</b>\n\n"
           text += "✅ Ora puoi utilizzare tutte le funzioni del bot!\n\n"
           text += "Usa /start per accedere al menu principale"
           
           keyboard = [
               [InlineKeyboardButton("🏠 Vai al Menu Principale", callback_data="back_to_menu")]
           ]
           
           await update.message.reply_text(
               text,
               parse_mode='HTML',
               reply_markup=InlineKeyboardMarkup(keyboard)
           )
           
           # Pulisci user_data
           context.user_data.clear()
           
       finally:
           db.close()
           
   except ValueError:
       await update.message.reply_text(
           "❌ Inserisci un numero valido",
           parse_mode='HTML'
       )
       return SETUP_LEAVE
   
   return ConversationHandler.END

# Conversation handler per il setup
setup_conversation_handler = ConversationHandler(
   entry_points=[CallbackQueryHandler(setup_start, pattern="^setup_start$")],
   states={
       SETUP_RANK: [CallbackQueryHandler(setup_rank, pattern="^rank_")],
       SETUP_COMMAND: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_command)],
       SETUP_IRPEF: [CallbackQueryHandler(setup_irpef, pattern="^irpef_")],
       SETUP_LEAVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, setup_leave)]
   },
   fallbacks=[CommandHandler("start", lambda u, c: ConversationHandler.END)],
   per_message=False
)
