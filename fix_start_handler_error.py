from telegram.ext import ContextTypes
from telegram import Update
#!/usr/bin/env python3
import subprocess

print("🔧 Fix errore start_handler")
print("=" * 50)

# Il problema è probabilmente in start_handler.py
print("\n1️⃣ Analizzo e correggo start_handler.py...")

# Leggi il file
with open('handlers/start_handler.py', 'r') as f:
    content = f.read()

# Il problema comune è l'accesso a update.message quando potrebbe essere update.callback_query
# Aggiungiamo controlli appropriati

# Trova la funzione start_command e sostituiscila con una versione più robusta
new_start_function = '''async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    # Gestisci sia messaggi che callback query
    if update.message:
        user = update.message.from_user
        chat_id = update.message.chat_id
    elif update.callback_query:
        user = update.callback_query.from_user
        chat_id = update.callback_query.message.chat_id
        await update.callback_query.answer()
    else:
        return
    
    # Get or create user
    db = SessionLocal()
    try:
        db_user = db.query(User).filter(User.telegram_id == str(user.id)).first()
        
        if not db_user:
            # Create new user
            db_user = User(
                telegram_id=str(user.id),
                chat_id=str(chat_id),
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db.add(db_user)
            db.commit()
            
            # Send welcome message with setup
            await send_welcome_setup(update, context, db_user)
        else:
            # Update chat_id if changed
            if db_user.chat_id != str(chat_id):
                db_user.chat_id = str(chat_id)
                db.commit()
            
            # Send dashboard
            await send_dashboard(update, context, db_user, db)
    except Exception as e:
        print(f"Errore in start_command: {e}")
        error_message = "❌ Si è verificato un errore. Riprova con /start"
        if update.message:
            await update.message.reply_text(error_message)
        elif update.callback_query:
            await update.callback_query.message.reply_text(error_message)
    finally:
        db.close()'''

# Trova l'inizio della funzione start_command
start_pos = content.find('async def start_command')
if start_pos == -1:
    print("❌ Non trovo la funzione start_command!")
else:
    # Trova la fine della funzione (prossima def o fine file)
    next_def = content.find('\nasync def', start_pos + 1)
    if next_def == -1:
        next_def = content.find('\ndef', start_pos + 1)
    
    if next_def != -1:
        # Sostituisci la funzione
        content = content[:start_pos] + new_start_function + '\n\n' + content[next_def:]
    else:
        # È l'ultima funzione
        content = content[:start_pos] + new_start_function
    
    print("✅ Funzione start_command aggiornata con gestione errori!")

# Correggi anche send_welcome_setup se necessario
if 'await update.message.reply_text' in content and 'send_welcome_setup' in content:
    content = content.replace(
        'await update.message.reply_text(',
        'await (update.message or update.callback_query.message).reply_text('
    )

# Salva il file
with open('handlers/start_handler.py', 'w') as f:
    f.write(content)

print("✅ File corretto!")

# Commit e push
print("\n2️⃣ Commit e push...")
subprocess.run("git add handlers/start_handler.py", shell=True)
subprocess.run('git commit -m "fix: gestione errori in start_command"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("\n🚀 Railway rifarà il deploy automaticamente")
print("⏰ Attendi 2-3 minuti e riprova /start su Telegram")
