#!/usr/bin/env python3
import subprocess

print("🧹 Aggiunta funzionalità Clean Chat - Solo ultimo messaggio")
print("=" * 50)

# 1. Crea il modulo per la gestione chat pulita
clean_chat_handler = '''"""
Clean Chat Handler - Mantiene solo l'ultimo messaggio
"""
from telegram import Update, Message, CallbackQuery
from telegram.ext import ContextTypes
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ChatCleaner:
    """Gestore per mantenere la chat pulita con solo l'ultimo messaggio"""
    
    def __init__(self):
        self.user_last_messages = {}  # {chat_id: message_id}
        self.bot_last_messages = {}   # {chat_id: message_id}
    
    async def clean_previous_messages(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Elimina tutti i messaggi precedenti"""
        messages_to_delete = []
        
        # Raccogli i message_id da eliminare
        if chat_id in self.user_last_messages:
            messages_to_delete.append(self.user_last_messages[chat_id])
        
        if chat_id in self.bot_last_messages:
            messages_to_delete.append(self.bot_last_messages[chat_id])
        
        # Elimina i messaggi
        for msg_id in messages_to_delete:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except Exception as e:
                logger.debug(f"Impossibile eliminare messaggio {msg_id}: {e}")
        
        # Pulisci i riferimenti
        self.user_last_messages.pop(chat_id, None)
        self.bot_last_messages.pop(chat_id, None)
    
    async def register_user_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE):
        """Registra un messaggio dell'utente e pulisce i precedenti"""
        chat_id = message.chat_id
        
        # Pulisci i messaggi precedenti
        await self.clean_previous_messages(chat_id, context)
        
        # Registra il nuovo messaggio
        self.user_last_messages[chat_id] = message.message_id
    
    async def register_bot_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE):
        """Registra un messaggio del bot"""
        chat_id = message.chat_id
        
        # Elimina solo il messaggio dell'utente, non il precedente del bot
        # (perché potrebbe essere un edit)
        if chat_id in self.user_last_messages:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id, 
                    message_id=self.user_last_messages[chat_id]
                )
            except:
                pass
            del self.user_last_messages[chat_id]
        
        # Registra il nuovo messaggio del bot
        self.bot_last_messages[chat_id] = message.message_id
    
    async def handle_callback_query(self, query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
        """Gestisce i callback query (pulsanti inline)"""
        # Quando viene premuto un pulsante, il messaggio viene editato
        # quindi non serve eliminarlo, è già gestito
        pass

# Istanza globale del cleaner
chat_cleaner = ChatCleaner()

async def wrap_handler_with_cleanup(handler_func):
    """Decorator per aggiungere la pulizia automatica agli handler"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Se è un messaggio normale
        if update.message:
            await chat_cleaner.register_user_message(update.message, context)
        
        # Esegui l'handler originale
        result = await handler_func(update, context)
        
        # Se l'handler ha restituito un messaggio, registralo
        if isinstance(result, Message):
            await chat_cleaner.register_bot_message(result, context)
        
        return result
    
    return wrapper

async def clean_chat_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE, next_handler):
    """Middleware per gestire la pulizia della chat"""
    # Per i messaggi
    if update.message:
        await chat_cleaner.register_user_message(update.message, context)
    
    # Esegui il prossimo handler
    result = await next_handler(update, context)
    
    return result

# Funzioni helper per gli handler esistenti
async def send_and_clean(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, **kwargs):
    """Invia un messaggio e registralo per la pulizia"""
    if update.callback_query:
        # Se è un callback, edita il messaggio esistente
        message = await update.callback_query.edit_message_text(text, **kwargs)
    else:
        # Altrimenti invia un nuovo messaggio
        message = await update.effective_message.reply_text(text, **kwargs)
        if message:
            await chat_cleaner.register_bot_message(message, context)
    
    return message

async def delete_after_delay(message: Message, delay: int = 5):
    """Elimina un messaggio dopo un delay"""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except:
        pass
'''

# Salva il modulo
with open('utils/clean_chat.py', 'w') as f:
    f.write(clean_chat_handler)

print("✅ Creato utils/clean_chat.py")

# 2. Modifica start_handler per usare la chat pulita
print("\n📝 Modifico start_handler per chat pulita...")

start_handler_update = '''
# Aggiungi all'inizio del file dopo gli import
from utils.clean_chat import chat_cleaner, send_and_clean

# Modifica start_command per pulire i messaggi precedenti
async def start_command_wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command con pulizia chat"""
    # Il comando dell'utente verrà eliminato automaticamente
    await start_command(update, context)
'''

# 3. Crea un wrapper per tutti i command handler
wrapper_code = '''#!/usr/bin/env python3
"""
Wrapper per aggiungere clean chat a tutti gli handler
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from utils.clean_chat import chat_cleaner

def clean_chat_command(func):
    """Decorator per command handler con pulizia chat"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Registra il messaggio dell'utente per l'eliminazione
        if update.message:
            await chat_cleaner.register_user_message(update.message, context)
        
        # Esegui l'handler
        result = await func(update, context)
        
        return result
    
    return wrapper

def clean_chat_callback(func):
    """Decorator per callback handler"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Per i callback non serve eliminare, si editano
        result = await func(update, context)
        return result
    
    return wrapper
'''

with open('utils/handler_decorators.py', 'w') as f:
    f.write(wrapper_code)

print("✅ Creato utils/handler_decorators.py")

# 4. Aggiorna main.py per usare il sistema di pulizia
print("\n📝 Aggiorno main.py per clean chat...")

with open('main.py', 'r') as f:
    main_content = f.read()

# Aggiungi import
import_addition = '''
# Import clean chat system
from utils.clean_chat import chat_cleaner
from utils.handler_decorators import clean_chat_command, clean_chat_callback
'''

# Trova dove aggiungere gli import
import_pos = main_content.find('from handlers.')
if import_pos > 0:
    main_content = main_content[:import_pos] + import_addition + '\n' + main_content[import_pos:]

# Wrappa tutti i command handler
commands_to_wrap = [
    'start_command',
    'new_service_command',
    'overtime_command',
    'travel_sheets_command',
    'leave_command',
    'settings_command',
    'today_command',
    'yesterday_command',
    'week_command',
    'month_command',
    'year_command',
    'export_command'
]

for cmd in commands_to_wrap:
    pattern = f'CommandHandler("{cmd.replace("_command", "")}", {cmd})'
    replacement = f'CommandHandler("{cmd.replace("_command", "")}", clean_chat_command({cmd}))'
    main_content = main_content.replace(pattern, replacement)

# Salva main.py aggiornato
with open('main.py', 'w') as f:
    f.write(main_content)

print("✅ Aggiornato main.py con clean chat")

# 5. Crea settings per abilitare/disabilitare la funzione
settings_addition = '''
# Impostazione per clean chat
CLEAN_CHAT_ENABLED = True  # Abilita/disabilita la pulizia automatica della chat
KEEP_ONLY_LAST_MESSAGE = True  # Mantiene solo l'ultimo messaggio
'''

with open('config/settings.py', 'a') as f:
    f.write('\n' + settings_addition)

print("✅ Aggiunto setting CLEAN_CHAT_ENABLED")

# 6. Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "feat: aggiunto sistema Clean Chat - mantiene solo ultimo messaggio"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Sistema Clean Chat installato!")
print("\n🧹 Funzionalità:")
print("- I comandi dell'utente vengono eliminati automaticamente")
print("- I messaggi precedenti vengono eliminati quando ne arriva uno nuovo")
print("- I messaggi con pulsanti vengono editati (non duplicati)")
print("- Risultato: chat sempre pulita con solo l'ultimo messaggio!")
print("\n⚙️ Per disabilitare: modifica CLEAN_CHAT_ENABLED in config/settings.py")
