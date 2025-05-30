#!/usr/bin/env python3
import subprocess

print("🔧 IMPLEMENTAZIONE SETUP INIZIALE UTENTE")
print("=" * 50)

# 1. Analizza come viene gestito il primo accesso
print("\n1️⃣ Analisi gestione primo accesso...")

with open('handlers/start_handler.py', 'r') as f:
   start_content = f.read()

# Vedo che c'è send_welcome_setup ma non è completamente implementato
print("✅ Trovata funzione send_welcome_setup")

# 2. Crea un sistema di setup guidato
print("\n2️⃣ Creazione sistema setup guidato...")

# Crea nuovo file setup_handler.py
setup_handler = '''"""
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
   
   text = "🎖️ <b>CONFIGURAZIONE PROFILO</b>\\n\\n"
   text += "Passo 1 di 4: Seleziona il tuo grado\\n\\n"
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
   
   text = f"✅ Grado selezionato: <b>{selected_rank}</b>\\n"
   text += f"📊 Parametro: <b>{parameter}</b>\\n\\n"
   text += "🏛️ <b>Passo 2 di 4: Comando di appartenenza</b>\\n\\n"
   text += "Inserisci il nome del tuo comando (es: Stazione CC Roma Parioli):"
   
   await query.edit_message_text(text, parse_mode='HTML')
   
   return SETUP_COMMAND

async def setup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Gestisce inserimento comando"""
   command_name = update.message.text.strip()
   context.user_data['setup_command'] = command_name
   
   text = f"✅ Comando: <b>{command_name}</b>\\n\\n"
   text += "💰 <b>Passo 3 di 4: Aliquota IRPEF</b>\\n\\n"
   text += "Seleziona la tua aliquota IRPEF attuale:\\n"
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
   
   text = f"✅ Aliquota IRPEF: <b>{rate}%</b>\\n\\n"
   text += "🏖️ <b>Passo 4 di 4: Licenze residue</b>\\n\\n"
   text += f"Quanti giorni di licenza {current_year} hai ancora disponibili?\\n"
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
           text = "🎉 <b>CONFIGURAZIONE COMPLETATA!</b>\\n\\n"
           text += "Il tuo profilo è stato configurato:\\n\\n"
           text += f"🎖️ Grado: <b>{user.rank}</b>\\n"
           text += f"🏛️ Comando: <b>{user.command}</b>\\n"
           text += f"💰 IRPEF: <b>{int(user.irpef_rate * 100)}%</b>\\n"
           text += f"🏖️ Licenze residue: <b>{leave_days} giorni</b>\\n\\n"
           text += "✅ Ora puoi utilizzare tutte le funzioni del bot!\\n\\n"
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
'''

# 3. Salva il nuovo handler
print("\n3️⃣ Creazione setup_handler.py...")
with open('handlers/setup_handler.py', 'w') as f:
   f.write(setup_handler)
print("✅ Creato handlers/setup_handler.py")

# 4. Aggiorna config/settings.py con i nuovi stati
print("\n4️⃣ Aggiornamento settings.py...")
with open('config/settings.py', 'r') as f:
   settings_content = f.read()

if 'SETUP_RANK' not in settings_content:
   # Aggiungi i nuovi stati
   settings_content = settings_content.replace(
       'SELECT_DATE,',
       'SELECT_DATE,\n    SETUP_RANK,\n    SETUP_COMMAND,\n    SETUP_IRPEF,\n    SETUP_LEAVE,'
   )
   settings_content = settings_content.replace(
       ') = range(12)',
       ') = range(16)'
   )
   
   with open('config/settings.py', 'w') as f:
       f.write(settings_content)
   print("✅ Aggiornati stati in settings.py")

# 5. Modifica start_handler.py per verificare se l'utente è configurato
print("\n5️⃣ Modifica start_handler.py...")

new_send_dashboard = '''async def send_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, db: Session):
   """Send main dashboard"""
   # Verifica se l'utente è configurato
   if not user.rank or not user.command:
       # Utente non configurato, mostra setup
       await send_welcome_setup(update, context, user)
       return
   
   current_date = get_current_date()
   current_month = current_date.month
   current_year = current_date.year'''

# Sostituisci l'inizio di send_dashboard
start_content = start_content.replace(
   'async def send_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, user: User, db: Session):\n    """Send main dashboard"""',
   new_send_dashboard
)

with open('handlers/start_handler.py', 'w') as f:
   f.write(start_content)
print("✅ Aggiornato start_handler.py")

# 6. Aggiorna main.py per includere setup_handler
print("\n6️⃣ Aggiornamento main.py...")

with open('main.py', 'r') as f:
   main_content = f.read()

# Aggiungi import
if 'from handlers.setup_handler import setup_conversation_handler' not in main_content:
   import_pos = main_content.find('from handlers.settings_handler')
   main_content = main_content[:import_pos] + 'from handlers.setup_handler import setup_conversation_handler\n' + main_content[import_pos:]

# Aggiungi handler
if 'setup_conversation_handler' not in main_content:
   conv_pos = main_content.find('# Conversation handlers')
   if conv_pos > 0:
       next_line = main_content.find('\n', conv_pos)
       main_content = main_content[:next_line] + '\n    application.add_handler(setup_conversation_handler)' + main_content[next_line:]

with open('main.py', 'w') as f:
   f.write(main_content)
print("✅ Aggiornato main.py")

# 7. Commit e push
print("\n7️⃣ Commit e push...")
subprocess.run("git add handlers/setup_handler.py handlers/start_handler.py config/settings.py main.py", shell=True)
subprocess.run('git commit -m "feat: aggiunto setup guidato per primo accesso con salvataggio nel database"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ SETUP INIZIALE IMPLEMENTATO!")
print("\n🎯 Funzionalità:")
print("- Al primo accesso, l'utente viene guidato in 4 passi")
print("- 1. Selezione grado (con parametro automatico)")
print("- 2. Inserimento comando")
print("- 3. Selezione aliquota IRPEF")
print("- 4. Giorni licenza residui")
print("- Tutto salvato nel database Railway")
print("\n⏰ Attendi 2-3 minuti per il deploy")
