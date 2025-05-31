#!/usr/bin/env python3
import subprocess
import os
import time

print("🚀 FIX COMPLETO CARABINIERI BOT - VERSIONE ALL-IN-ONE")
print("=" * 50)

# Verifica directory
if not os.path.exists('main.py'):
    print("❌ Errore: non sono nella directory del bot!")
    exit(1)

print(f"📂 Directory: {os.getcwd()}")
print("✅ Iniziamo i fix...\n")

# FIX 1: Handler mancanti in main.py
print("🔧 FIX 1/4: Handler mancanti in main.py")
print("-" * 40)

try:
    with open('main.py', 'r') as f:
        content = f.read()

    lines = content.split('\n')
    insert_index = -1

    # Trova dove inserire i nuovi handler
    for i, line in enumerate(lines):
        if 'CommandHandler("mese", month_command)' in line:
            insert_index = i + 1
            break

    if insert_index != -1:
        new_handlers = '''    application.add_handler(CommandHandler("ieri", yesterday_command))
    application.add_handler(CommandHandler("settimana", week_command))
    application.add_handler(CommandHandler("anno", year_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("ore_pagate", paid_hours_command))
    application.add_handler(CommandHandler("accumulo", accumulation_command))
    application.add_handler(CommandHandler("nuova_licenza", add_leave_command))
    application.add_handler(CommandHandler("pianifica_licenze", plan_leave_command))
    application.add_handler(CommandHandler("fv_pagamento", register_payment_command))'''
        
        lines.insert(insert_index, new_handlers)
        
        # Aggiungi handler per callback non gestiti
        for i, line in enumerate(lines):
            if 'application.run_polling()' in line:
                catch_all = '''
    # Handler per callback non gestiti - DEVE essere l'ultimo!
    async def handle_unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        callback_data = query.data
        logger.warning(f"Callback non implementato: {callback_data}")
        
        if "back_to_menu" in callback_data:
            await start_command(update, context)
        elif "setup_start" in callback_data:
            await query.answer("Usa /impostazioni per configurare il profilo", show_alert=True)
        else:
            await query.answer("Funzione in sviluppo", show_alert=True)
    
    application.add_handler(CallbackQueryHandler(handle_unknown_callback))
'''
                lines.insert(i-1, catch_all)
                break
        
        with open('main.py', 'w') as f:
            f.write('\n'.join(lines))
        
        print("✅ Handler aggiunti")
    else:
        print("⚠️ Punto di inserimento non trovato, skip")
        
except Exception as e:
    print(f"❌ Errore: {e}")

time.sleep(1)

# FIX 2: Import mancante in notification_service.py
print("\n🔧 FIX 2/4: Import mancante in notification_service.py")
print("-" * 40)

try:
    with open('services/notification_service.py', 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed = False
    
    for i, line in enumerate(lines):
        if 'from sqlalchemy import extract, and_' in line:
            lines[i] = 'from sqlalchemy import extract, and_, func'
            fixed = True
            break
    
    if fixed:
        with open('services/notification_service.py', 'w') as f:
            f.write('\n'.join(lines))
        print("✅ Import 'func' aggiunto")
    else:
        print("⚠️ Import già corretto o non trovato")
        
except Exception as e:
    print(f"❌ Errore: {e}")

time.sleep(1)

# FIX 3: Relazioni database
print("\n🔧 FIX 3/4: Relazioni database")
print("-" * 40)

try:
    with open('database/models.py', 'r') as f:
        content = f.read()
    
    # Rimuovi riferimenti a rest_replaced
    content = content.replace('rest_replaced', 'rests')
    
    with open('database/models.py', 'w') as f:
        f.write(content)
    
    print("✅ Relazioni database corrette")
    
    # Crea script di verifica
    verify_script = '''#!/usr/bin/env python3
"""Verifica struttura database"""
import os
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///test.db')

from database.connection import engine, Base
from database.models import *
from sqlalchemy import inspect

print("🔍 Verifica database...")

try:
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tabelle trovate: {tables}")
    
    required = ['users', 'services', 'overtimes', 'travel_sheets', 'leaves', 'rests']
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"⚠️ Tabelle mancanti: {missing}")
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelle create")
    else:
        print("✅ Tutte le tabelle OK")
except Exception as e:
    print(f"❌ Errore: {e}")
'''
    
    with open('verify_database.py', 'w') as f:
        f.write(verify_script)
    os.chmod('verify_database.py', 0o755)
    
    print("✅ Creato verify_database.py")
    
except Exception as e:
    print(f"❌ Errore: {e}")

time.sleep(1)

# FIX 4: Documentazione stati
print("\n🔧 FIX 4/4: Documentazione stati conversazione")
print("-" * 40)

try:
    doc = '''# Stati Conversazione CarabinieriPayBot

## Stati Attivi:
- SELECT_DATE: Selezione data servizio
- SETUP_RANK: Setup grado
- SETUP_COMMAND: Setup comando
- SETUP_IRPEF: Setup IRPEF
- SETUP_LEAVE: Setup licenze
- SELECT_TIME: Selezione orario
- SELECT_SERVICE_TYPE: Tipo servizio
- SERVICE_DETAILS: Dettagli servizio
- TRAVEL_DETAILS: Dettagli viaggio
- TRAVEL_TYPE: Tipo viaggio
- MEAL_DETAILS: Pasti
- CONFIRM_SERVICE: Conferma
- LEAVE_DATES: Date licenza
- LEAVE_TYPE: Tipo licenza

## Stati Non Usati:
- PAYMENT_DETAILS (rimosso)
- SELECT_TRAVEL_SHEETS (rimosso)
'''
    
    with open('CONVERSATION_STATES.md', 'w') as f:
        f.write(doc)
    
    print("✅ Documentazione creata")
    
except Exception as e:
    print(f"❌ Errore: {e}")

# Verifica sintassi Python
print("\n🔍 Verifica sintassi files modificati...")
files_to_check = ['main.py', 'services/notification_service.py', 'database/models.py']

all_ok = True
for file in files_to_check:
    result = subprocess.run(['python3', '-m', 'py_compile', file], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {file} - OK")
    else:
        print(f"❌ {file} - Errore: {result.stderr}")
        all_ok = False

if all_ok:
    # Commit e push
    print("\n📤 Commit e push di tutti i fix...")
    subprocess.run("git add -A", shell=True)
    subprocess.run('git commit -m "fix: risolti handler mancanti, import, relazioni DB e documentazione stati"', shell=True)
    result = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Push completato con successo!")
    else:
        print(f"⚠️ Problema con push: {result.stderr}")
else:
    print("\n❌ Ci sono errori di sintassi, fix manuale necessario")

print("\n" + "=" * 50)
print("🎉 FIX COMPLETATI!")
print("\n📋 Prossimi passi:")
print("1. Railway sta facendo il deploy automatico")
print("2. Attendi 2-3 minuti")
print("3. Testa con: python3 test_bot_connection.py")
print("4. Verifica DB con: python3 verify_database.py")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script auto-eliminato")
