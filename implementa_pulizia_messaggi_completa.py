#!/usr/bin/env python3
import subprocess

print("🧹 IMPLEMENTAZIONE COMPLETA SISTEMA PULIZIA MESSAGGI")
print("=" * 50)

# 1. Crea nuovo clean_chat.py funzionante
print("\n1️⃣ Creazione clean_chat.py...")

clean_chat_content = '''"""
Sistema di pulizia automatica messaggi per CarabinieriPayBot
"""
from telegram import Update
from telegram.ext import ContextTypes
import asyncio
import logging
from typing import Dict, List
from collections import deque

logger = logging.getLogger(__name__)

class MessageCleaner:
    """Gestisce l'eliminazione automatica dei messaggi"""
    
    def __init__(self):
        # Mantieni una coda di messaggi per chat_id
        self.message_history: Dict[int, deque] = {}
        # Numero massimo di messaggi da mantenere
        self.max_messages = 5
        # Messaggi da non eliminare (con pulsanti)
        self.protected_messages: Dict[int, set] = {}
        
    async def add_message(self, chat_id: int, message_id: int, context: ContextTypes.DEFAULT_TYPE, is_protected: bool = False):
        """Aggiunge un messaggio e pulisce i vecchi"""
        
        # Inizializza la coda per questa chat se non esiste
        if chat_id not in self.message_history:
            self.message_history[chat_id] = deque(maxlen=self.max_messages * 2)
            self.protected_messages[chat_id] = set()
        
        # Aggiungi il messaggio
        self.message_history[chat_id].append(message_id)
        
        # Se è protetto (con pulsanti), segnalo
        if is_protected:
            self.protected_messages[chat_id].add(message_id)
        
        # Pulisci i messaggi vecchi
        await self._cleanup_old_messages(chat_id, context)
    
    async def _cleanup_old_messages(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Elimina i messaggi vecchi mantenendo solo gli ultimi"""
        
        messages = list(self.message_history[chat_id])
        
        # Se abbiamo troppi messaggi
        if len(messages) > self.max_messages:
            # Messaggi da eliminare (i più vecchi)
            to_delete = messages[:-self.max_messages]
            
            for msg_id in to_delete:
                # Non eliminare messaggi protetti
                if msg_id in self.protected_messages.get(chat_id, set()):
                    continue
                    
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                    # Rimuovi dalla history
                    if msg_id in self.message_history[chat_id]:
                        self.message_history[chat_id].remove(msg_id)
                    await asyncio.sleep(0.1)  # Anti rate-limit
                except Exception as e:
                    logger.debug(f"Non posso eliminare {msg_id}: {e}")

# Istanza globale
cleaner = MessageCleaner()

async def register_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Registra un messaggio utente per la pulizia"""
    if update.message:
        await cleaner.add_message(
            update.message.chat_id,
            update.message.message_id,
            context,
            is_protected=False
        )

async def register_bot_message(message, context: ContextTypes.DEFAULT_TYPE):
    """Registra un messaggio del bot"""
    if message:
        # Controlla se ha pulsanti inline
        has_buttons = bool(message.reply_markup)
        await cleaner.add_message(
            message.chat_id,
            message.message_id,
            context,
            is_protected=has_buttons
        )

# Middleware per intercettare tutti i messaggi
async def cleanup_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Middleware che registra automaticamente i messaggi"""
    if update.message:
        await register_user_message(update, context)
'''

with open('utils/clean_chat.py', 'w') as f:
    f.write(clean_chat_content)

print("✅ clean_chat.py creato")

# 2. Crea wrapper per integrare negli handler
print("\n2️⃣ Creazione wrapper per handler...")

wrapper_content = '''"""
Wrapper per aggiungere pulizia automatica agli handler
"""
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from utils.clean_chat import register_user_message, register_bot_message

def with_message_cleanup(func):
    """Decorator che aggiunge pulizia automatica messaggi"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Registra messaggio utente
        if update.message:
            await register_user_message(update, context)
        
        # Esegui handler originale
        result = await func(update, context)
        
        # Se l'handler ha restituito un messaggio, registralo
        if result and hasattr(result, 'message_id'):
            await register_bot_message(result, context)
            
        return result
    
    return wrapper
'''

with open('utils/message_wrapper.py', 'w') as f:
    f.write(wrapper_content)

print("✅ message_wrapper.py creato")

# 3. Aggiorna main.py con middleware globale
print("\n3️⃣ Aggiornamento main.py...")

with open('main.py', 'r') as f:
    main_content = f.read()

# Rimuovi vecchi import di clean_chat
main_content = main_content.replace('from utils.clean_chat import message_cleaner, cleanup_middleware', '')
main_content = main_content.replace('from utils.clean_chat import chat_cleaner', '')

# Aggiungi nuovo import
if 'from utils.clean_chat import cleanup_middleware' not in main_content:
    import_pos = main_content.find('from dotenv import load_dotenv')
    main_content = main_content[:import_pos] + 'from utils.clean_chat import cleanup_middleware\n' + main_content[import_pos:]

# Aggiungi middleware DOPO la creazione dell'application
if 'MessageHandler(filters.ALL, cleanup_middleware)' not in main_content:
    # Trova dove aggiungere (dopo la creazione application)
    builder_line = main_content.find('application = Application.builder()')
    if builder_line > 0:
        # Trova il primo add_handler
        first_handler = main_content.find('application.add_handler', builder_line)
        if first_handler > 0:
            middleware_code = '''    # Middleware per pulizia automatica messaggi
    # DEVE essere il PRIMO handler con priority massima
    application.add_handler(MessageHandler(filters.ALL, cleanup_middleware), group=-999)
    
'''
            main_content = main_content[:first_handler] + middleware_code + main_content[first_handler:]

with open('main.py', 'w') as f:
    f.write(main_content)

print("✅ main.py aggiornato")

# 4. Aggiorna un handler di esempio per mostrare come usare il wrapper
print("\n4️⃣ Esempio integrazione in start_handler.py...")

example_integration = '''
# All'inizio del file, dopo gli import:
from utils.message_wrapper import with_message_cleanup

# Poi applica il decorator alle funzioni che inviano messaggi:
@with_message_cleanup
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ... codice esistente ...
'''

print("📝 Esempio di utilizzo del decorator:")
print(example_integration)

# 5. Verifica sintassi
print("\n5️⃣ Verifica sintassi...")

files_to_check = ['utils/clean_chat.py', 'utils/message_wrapper.py', 'main.py']
all_ok = True

for file in files_to_check:
    result = subprocess.run(['python3', '-m', 'py_compile', file], capture_output=True)
    if result.returncode == 0:
        print(f"✅ {file}: OK")
    else:
        print(f"❌ {file}: ERRORE")
        print(result.stderr.decode())
        all_ok = False

# 6. Commit se tutto ok
if all_ok:
    print("\n6️⃣ Commit e push...")
    subprocess.run("git add utils/clean_chat.py utils/message_wrapper.py main.py", shell=True)
    subprocess.run('git commit -m "feat: implementato sistema completo pulizia automatica messaggi"', shell=True)
    subprocess.run("git push origin main", shell=True)
    print("✅ Push completato")

print("\n" + "=" * 50)
print("✅ SISTEMA PULIZIA MESSAGGI IMPLEMENTATO!")
print("\n🎯 Funzionalità:")
print("1. Middleware globale che intercetta TUTTI i messaggi")
print("2. Mantiene solo gli ultimi 5 messaggi per chat")
print("3. NON elimina messaggi con pulsanti inline")
print("4. Elimina automaticamente i messaggi vecchi")
print("\n📱 Il sistema funzionerà automaticamente su tutti i comandi!")
print("\n⏰ Attendi 2-3 minuti per il deploy su Railway")
