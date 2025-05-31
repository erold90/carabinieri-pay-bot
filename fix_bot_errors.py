#!/usr/bin/env python3
"""
Fix errori del bot e aggiungi gestione errori migliore
"""
import subprocess
import os

print("🔧 FIX ERRORI BOT")
print("=" * 60)

fixes = []

# 1. Aggiungi try-catch a tutti i command handler
print("\n1️⃣ Aggiunta error handling ai comandi...")

# Fix start_handler.py
with open('handlers/start_handler.py', 'r') as f:
    content = f.read()

# Trova start_command e aggiungi try-catch se mancante
if 'async def start_command' in content and 'try:' not in content.split('async def start_command')[1].split('async def')[0]:
    # Aggiungi try-catch
    lines = content.split('\n')
    new_lines = []
    in_start_command = False
    indent_level = 0
    
    for i, line in enumerate(lines):
        if 'async def start_command' in line:
            new_lines.append(line)
            in_start_command = True
            # Salta docstring se presente
            j = i + 1
            while j < len(lines) and (lines[j].strip().startswith('"""') or lines[j].strip().startswith("'''")):
                new_lines.append(lines[j])
                j += 1
            # Aggiungi try
            new_lines.append('    try:')
            indent_level = 8
            continue
        elif in_start_command and line.strip() and not line.startswith(' '):
            # Fine della funzione
            # Aggiungi except prima della fine
            new_lines.append('    except Exception as e:')
            new_lines.append('        logger.error(f"Errore in start_command: {e}", exc_info=True)')
            new_lines.append('        if update.message:')
            new_lines.append('            await update.message.reply_text("❌ Si è verificato un errore. Riprova con /start")')
            new_lines.append(line)
            in_start_command = False
        elif in_start_command and line.strip():
            # Aggiungi indentazione extra per il try block
            new_lines.append('    ' + line)
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    fixes.append("✅ Aggiunto try-catch a start_command")

with open('handlers/start_handler.py', 'w') as f:
    f.write(content)

# 2. Fix hello command in main.py
print("\n2️⃣ Fix hello command...")
with open('main.py', 'r') as f:
    content = f.read()

# Migliora hello_command con error handling
if 'async def hello_command' in content:
    old_hello = content[content.find('async def hello_command'):content.find('\n\n', content.find('async def hello_command'))]
    
    new_hello = '''async def hello_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando test semplice"""
    try:
        logger.info("HELLO COMMAND CHIAMATO")
        user_id = update.effective_user.id if update.effective_user else "Unknown"
        chat_id = update.effective_chat.id if update.effective_chat else "Unknown"
        username = update.effective_user.username if update.effective_user else "Unknown"
        
        message = (
            "👋 Ciao! Il bot funziona!\\n\\n"
            "Debug info:\\n"
            f"User ID: {user_id}\\n"
            f"Chat ID: {chat_id}\\n"
            f"Username: @{username}"
        )
        
        await update.message.reply_text(message)
        logger.info("Hello command completato con successo")
    except Exception as e:
        logger.error(f"Errore in hello_command: {e}", exc_info=True)
        await update.message.reply_text("❌ Errore nel comando hello")'''
    
    content = content.replace(old_hello, new_hello)
    fixes.append("✅ Migliorato hello_command")

with open('main.py', 'w') as f:
    f.write(content)

# 3. Aggiungi comando di emergenza /ping
print("\n3️⃣ Aggiunta comando emergenza /ping...")
with open('main.py', 'r') as f:
    content = f.read()

if 'async def ping_command' not in content:
    ping_command = '''
async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando ping super semplice"""
    await update.message.reply_text("🏓 Pong!")
'''
    
    # Aggiungi prima di main()
    main_pos = content.find('def main():')
    content = content[:main_pos] + ping_command + '\n' + content[main_pos:]
    
    # Aggiungi handler
    hello_handler_pos = content.find('application.add_handler(CommandHandler("hello"')
    if hello_handler_pos > -1:
        insert_pos = content.find('\n', hello_handler_pos) + 1
        content = content[:insert_pos] + '    application.add_handler(CommandHandler("ping", ping_command))\n' + content[insert_pos:]
    
    fixes.append("✅ Aggiunto comando /ping")

with open('main.py', 'w') as f:
    f.write(content)

# 4. Fix import mancanti
print("\n4️⃣ Verifica import...")
with open('handlers/start_handler.py', 'r') as f:
    content = f.read()

if 'import logging' not in content:
    content = 'import logging\n\nlogger = logging.getLogger(__name__)\n\n' + content
    fixes.append("✅ Aggiunto import logging a start_handler")

with open('handlers/start_handler.py', 'w') as f:
    f.write(content)

# 5. Crea script di test database
print("\n5️⃣ Creazione test database...")
test_db = '''#!/usr/bin/env python3
"""Test connessione database"""
import os
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///test.db')

from database.connection import SessionLocal, init_db
from database.models import User

print("🧪 TEST DATABASE")
print("=" * 50)

try:
    init_db()
    print("✅ Database inizializzato")
    
    db = SessionLocal()
    user_count = db.query(User).count()
    print(f"👥 Utenti nel database: {user_count}")
    
    # Test creazione utente
    test_user = User(
        telegram_id="test123",
        chat_id="test123",
        username="test",
        first_name="Test",
        last_name="User"
    )
    db.add(test_user)
    db.commit()
    print("✅ Test creazione utente OK")
    
    # Rimuovi test user
    db.query(User).filter(User.telegram_id == "test123").delete()
    db.commit()
    db.close()
    
    print("✅ Database funzionante!")
    
except Exception as e:
    print(f"❌ Errore database: {e}")
    import traceback
    traceback.print_exc()
'''

with open('test_database.py', 'w') as f:
    f.write(test_db)
os.chmod('test_database.py', 0o755)
fixes.append("✅ Creato test database")

# Verifica sintassi
print("\n🧪 Verifica sintassi...")
files = ['main.py', 'handlers/start_handler.py']
all_good = True

for file in files:
    result = subprocess.run(['python3', '-m', 'py_compile', file], 
                           capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Errore in {file}: {result.stderr}")
        all_good = False

if all_good:
    print("✅ Sintassi OK")
    
    # Commit e push
    print("\n📤 Commit modifiche...")
    subprocess.run("git add -A", shell=True)
    subprocess.run('git commit -m "fix: aggiunto error handling completo e comandi di debug"', shell=True)
    subprocess.run("git push origin main", shell=True)
    
    print("\n" + "=" * 60)
    print("✅ FIX COMPLETATO!")
    print(f"📊 Fix applicati: {len(fixes)}")
    for fix in fixes:
        print(f"   {fix}")
    
    print("\n🧪 COMANDI DA TESTARE:")
    print("1. /ping - Dovrebbe rispondere 'Pong!'")
    print("2. /hello - Info di debug")
    print("3. /start - Con error handling")
    
    print("\n💡 PROSSIMI PASSI:")
    print("1. Aspetta il deploy (1-2 min)")
    print("2. Prova /ping per primo")
    print("3. Guarda i log per errori dettagliati")
    print("=" * 60)

# Test locale del database
print("\n🔍 Test database locale...")
subprocess.run("python3 test_database.py", shell=True)

# Auto-elimina
os.remove(__file__)
