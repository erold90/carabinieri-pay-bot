#!/usr/bin/env python3
"""
Debug del comando /start
"""
import subprocess
import os

print("🔍 DEBUG COMANDO START")
print("=" * 60)

# Controlla start_handler.py
print("\n1️⃣ Verifica start_handler.py...")
with open('handlers/start_handler.py', 'r') as f:
    content = f.read()
    
# Cerca problemi comuni
issues = []

# Verifica che start_command sia async
if 'async def start_command' not in content:
    issues.append("❌ start_command non è async")

# Verifica che ci sia send_dashboard o send_welcome_setup
if 'send_dashboard' not in content and 'send_welcome_setup' not in content:
    issues.append("❌ Manca send_dashboard o send_welcome_setup")

# Verifica che SessionLocal sia usato correttamente
if 'SessionLocal()' in content and 'finally:' not in content:
    issues.append("⚠️ SessionLocal potrebbe non essere chiuso correttamente")

print(f"Trovati {len(issues)} potenziali problemi")
for issue in issues:
    print(f"  {issue}")

# 2. Aggiungi più log a start_command
print("\n2️⃣ Aggiunta log dettagliati...")
with open('handlers/start_handler.py', 'r') as f:
    lines = f.readlines()

# Trova start_command
for i, line in enumerate(lines):
    if 'async def start_command' in line:
        # Aggiungi log all'inizio della funzione
        j = i + 1
        while j < len(lines) and lines[j].strip().startswith(('"""', "'''")):
            j += 1
        
        # Inserisci log dopo la docstring
        indent = '    '
        if j < len(lines):
            # Aggiungi log se non già presente
            if 'logger.info("Start command received")' not in lines[j]:
                lines.insert(j, f'{indent}logger.info("🚀 START COMMAND CHIAMATO!")\n')
                lines.insert(j+1, f'{indent}logger.info(f"User: {{update.effective_user.id if update.effective_user else \'Unknown\'}}")\n')
                lines.insert(j+2, f'{indent}logger.info(f"Chat: {{update.effective_chat.id if update.effective_chat else \'Unknown\'}}")\n')
                print("✅ Aggiunti log di debug")

# Salva il file
with open('handlers/start_handler.py', 'w') as f:
    f.writelines(lines)

# 3. Crea comando test semplificato
print("\n3️⃣ Creazione comando /hello di test...")
test_handler = '''
# Aggiungi questo handler di test in main.py
async def hello_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando test semplice"""
    logger.info("HELLO COMMAND CHIAMATO")
    await update.message.reply_text(
        "👋 Ciao! Il bot funziona!\\n\\n"
        "Debug info:\\n"
        f"User ID: {update.effective_user.id}\\n"
        f"Chat ID: {update.effective_chat.id}\\n"
        f"Username: @{update.effective_user.username}"
    )
'''

# Aggiungi a main.py
with open('main.py', 'r') as f:
    content = f.read()

# Aggiungi la funzione hello prima di main()
if 'async def hello_command' not in content:
    main_pos = content.find('def main():')
    if main_pos > -1:
        content = content[:main_pos] + test_handler + '\n' + content[main_pos:]
        print("✅ Aggiunto hello_command")

# Aggiungi l'handler
if 'CommandHandler("hello", hello_command)' not in content:
    handlers_section = content.find('application.add_handler(CommandHandler("start"')
    if handlers_section > -1:
        insert_pos = content.find('\n', handlers_section) + 1
        content = content[:insert_pos] + '    application.add_handler(CommandHandler("hello", hello_command))\n' + content[insert_pos:]
        print("✅ Aggiunto handler /hello")

with open('main.py', 'w') as f:
    f.write(content)

# 4. Fix potenziale problema con update.callback_query
print("\n4️⃣ Fix gestione callback_query in start_command...")
with open('handlers/start_handler.py', 'r') as f:
    content = f.read()

# Assicurati che gestisca sia messaggi che callback
if 'if update.callback_query:' in content and 'await update.callback_query.answer()' not in content:
    # Aggiungi answer() per callback queries
    content = content.replace(
        'if update.callback_query:',
        'if update.callback_query:\n        await update.callback_query.answer()'
    )
    print("✅ Aggiunto callback answer")

with open('handlers/start_handler.py', 'w') as f:
    f.write(content)

# 5. Verifica sintassi
print("\n5️⃣ Verifica sintassi...")
files_to_check = ['main.py', 'handlers/start_handler.py']
all_good = True

for file in files_to_check:
    result = subprocess.run(['python3', '-m', 'py_compile', file], 
                           capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Errore in {file}:")
        print(result.stderr)
        all_good = False
    else:
        print(f"✅ {file} OK")

if all_good:
    # Commit e push
    print("\n📤 Commit modifiche...")
    subprocess.run("git add -A", shell=True)
    subprocess.run('git commit -m "fix: aggiunto debug per comando start e comando test /hello"', shell=True)
    subprocess.run("git push origin main", shell=True)
    
    print("\n" + "=" * 60)
    print("✅ DEBUG COMPLETATO!")
    print("\n🧪 PROVA QUESTI COMANDI:")
    print("1. /hello - Dovrebbe rispondere con un messaggio di test")
    print("2. /start - Controlla i log per vedere cosa succede")
    print("\n📊 NEI LOG DOVRESTI VEDERE:")
    print("- 🚀 START COMMAND CHIAMATO!")
    print("- User ID e Chat ID")
    print("- Eventuali errori")
    print("=" * 60)
else:
    print("\n❌ Ci sono errori di sintassi da correggere")

# Auto-elimina
os.remove(__file__)
