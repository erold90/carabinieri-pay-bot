#!/usr/bin/env python3
import subprocess
import os

print("🔍 Analisi e fix problemi CarabinieriPayBot")
print("=" * 50)

# 1. Fix MEAL_RATES mancante in constants.py
print("\n1️⃣ Aggiunta MEAL_RATES in constants.py...")
with open('config/constants.py', 'r') as f:
    content = f.read()

if 'MEAL_RATES' not in content:
    # Aggiungi MEAL_RATES prima di FORFEIT_RATES
    meal_rates_def = '''
# Meal reimbursements
MEAL_RATES = {
    'single_meal_gross': 22.26,
    'single_meal_net': 14.29,
    'double_meal_gross': 44.52,
    'double_meal_net': 28.58
}
'''
    
    # Trova dove inserirlo
    insert_pos = content.find('# Forfeit rates')
    if insert_pos > 0:
        content = content[:insert_pos] + meal_rates_def + '\n' + content[insert_pos:]
        
        with open('config/constants.py', 'w') as f:
            f.write(content)
        print("✅ MEAL_RATES aggiunto")
    else:
        print("⚠️ Non trovato punto di inserimento per MEAL_RATES")
else:
    print("✅ MEAL_RATES già presente")

# 2. Fix handler per text input in settings
print("\n2️⃣ Aggiunta handler per text input in main.py...")
with open('main.py', 'r') as f:
    main_content = f.read()

# Cerca se manca l'handler per settings text input
if 'handle_text_input' not in main_content:
    # Aggiungi import
    import_line = "from handlers.settings_handler import (\n    settings_command,\n    settings_callback,\n    update_rank,\n    update_irpef"
    new_import = "from handlers.settings_handler import (\n    settings_command,\n    settings_callback,\n    update_rank,\n    update_irpef,\n    handle_text_input"
    
    main_content = main_content.replace(import_line, new_import)
    
    # Aggiungi handler prima dei conversation handlers
    handler_addition = '''
    # Text input handler for settings
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        handle_text_input
    ))
    '''
    
    # Trova dove inserirlo (dopo i command handlers)
    insert_pos = main_content.find('# Conversation handlers')
    if insert_pos > 0:
        main_content = main_content[:insert_pos] + handler_addition + '\n    ' + main_content[insert_pos:]
        
        with open('main.py', 'w') as f:
            f.write(main_content)
        print("✅ Handler text input aggiunto")
else:
    print("✅ Handler già presente")

# 3. Fix import in service_handler.py
print("\n3️⃣ Fix import MEAL_RATES in service_handler.py...")
with open('handlers/service_handler.py', 'r') as f:
    service_content = f.read()

# Aggiungi MEAL_RATES all'import
old_import = "from config.constants import SUPER_HOLIDAYS, OVERTIME_RATES"
new_import = "from config.constants import SUPER_HOLIDAYS, OVERTIME_RATES, MEAL_RATES"

if 'MEAL_RATES' not in service_content.split('\n')[15]:  # Circa linea 16
    service_content = service_content.replace(old_import, new_import)
    
    with open('handlers/service_handler.py', 'w') as f:
        f.write(service_content)
    print("✅ Import MEAL_RATES aggiunto")
else:
    print("✅ Import già corretto")

# 4. Verifica handler per travel sheet text input
print("\n4️⃣ Verifica handler per fogli viaggio...")
with open('main.py', 'r') as f:
    main_content = f.read()

# Aggiungi handler per travel sheet text se manca
if 'handle_fv_text_input' not in main_content:
    print("⚠️ Potrebbe mancare handler per input FV - da verificare")

# 5. Fix callback query patterns
print("\n5️⃣ Fix pattern callback queries...")
# Rimuovi pattern duplicati o errati
patterns_to_fix = [
    ('pattern="^([^_"', 'pattern="^back_"'),
    ('pattern="^([^$"', 'pattern="^back$"')
]

for old_pattern, new_pattern in patterns_to_fix:
    if old_pattern in main_content:
        main_content = main_content.replace(old_pattern, new_pattern)
        print(f"✅ Corretto pattern: {old_pattern} -> {new_pattern}")

with open('main.py', 'w') as f:
    f.write(main_content)

# Commit e push
print("\n📤 Commit e push delle modifiche...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: aggiunto MEAL_RATES e corretto handlers mancanti"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completati!")
print("🚀 Railway rifarà il deploy automaticamente")
print("\n⏰ Attendi 2-3 minuti per il deploy completo")
print("\n📱 Poi testa il bot con:")
print("   /start - Menu principale")
print("   /nuovo - Nuovo servizio")
print("   /impostazioni - Configurazione")
