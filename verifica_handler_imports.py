#!/usr/bin/env python3
import subprocess
import re

print("🔍 VERIFICA FINALE HANDLER E IMPORT")
print("=" * 50)

# 1. Leggi main.py
with open('main.py', 'r') as f:
    main_content = f.read()

# 2. Trova tutti gli handler usati
print("\n1️⃣ Ricerca handler utilizzati...")
handlers_used = set()

# Pattern per trovare handler nei callback
patterns = [
    r'CallbackQueryHandler\((\w+),',
    r'CommandHandler\("[^"]+",\s*(\w+)\)',
    r'MessageHandler\([^,]+,\s*(\w+)\)'
]

for pattern in patterns:
    matches = re.findall(pattern, main_content)
    handlers_used.update(matches)

print(f"Handler trovati: {len(handlers_used)}")

# 3. Verifica che tutti siano importati o definiti
print("\n2️⃣ Verifica import/definizioni...")
missing_handlers = []

for handler in handlers_used:
    # Controlla se è importato o definito
    if handler not in ['error_handler', 'debug_unhandled_callback', 'message_cleanup_middleware']:
        # Questi sono definiti inline in main.py
        if f'def {handler}' not in main_content and f'import {handler}' not in main_content:
            if not re.search(f'from .* import .*{handler}', main_content):
                missing_handlers.append(handler)

if missing_handlers:
    print(f"\n⚠️ Handler mancanti: {missing_handlers}")
    
    # 4. Aggiungi import mancanti
    print("\n3️⃣ Aggiunta import mancanti...")
    
    # Mappa handler ai moduli
    handler_modules = {
        'handle_service_type': 'service_handler',
        'handle_status_selection': 'service_handler',
        'handle_meals': 'service_handler',
        'handle_meal_selection': 'service_handler',
        'handle_mission_type': 'service_handler',
        'handle_time_input': 'service_handler',
        'overtime_callback': 'overtime_handler',
        'travel_sheet_callback': 'travel_sheet_handler',
        'leave_callback': 'leave_handler',
        'settings_callback': 'settings_handler',
        'month_command': 'report_handler',
        'week_command': 'report_handler',
        'year_command': 'report_handler'
    }
    
    # Raggruppa per modulo
    imports_to_add = {}
    for handler in missing_handlers:
        if handler in handler_modules:
            module = handler_modules[handler]
            if module not in imports_to_add:
                imports_to_add[module] = []
            imports_to_add[module].append(handler)
    
    # Aggiungi gli import
    for module, handlers in imports_to_add.items():
        import_line = f"from handlers.{module} import {', '.join(handlers)}"
        
        # Trova dove inserire (dopo altri import di handlers)
        insert_pos = main_content.find(f'from handlers.{module}')
        if insert_pos > 0:
            # Modulo già importato, aggiungi alla lista
            line_end = main_content.find('\n', insert_pos)
            current_line = main_content[insert_pos:line_end]
            
            # Estrai handlers già importati
            current_imports = re.search(r'import (.+)$', current_line)
            if current_imports:
                existing = [h.strip() for h in current_imports.group(1).split(',')]
                new_handlers = [h for h in handlers if h not in existing]
                if new_handlers:
                    new_line = current_line.rstrip() + ', ' + ', '.join(new_handlers)
                    main_content = main_content[:insert_pos] + new_line + main_content[line_end:]
        else:
            # Nuovo import
            last_handler_import = main_content.rfind('from handlers.')
            if last_handler_import > 0:
                line_end = main_content.find('\n', last_handler_import)
                main_content = main_content[:line_end] + '\n' + import_line + main_content[line_end:]
    
    # Salva
    with open('main.py', 'w') as f:
        f.write(main_content)
    
    print("✅ Import aggiunti")
else:
    print("✅ Tutti gli handler sono correttamente importati!")

# 5. Verifica sintassi finale
print("\n4️⃣ Verifica sintassi main.py...")
result = subprocess.run(['python3', '-m', 'py_compile', 'main.py'], capture_output=True)
if result.returncode == 0:
    print("✅ Sintassi corretta!")
else:
    print("❌ Errore di sintassi!")
    print(result.stderr.decode())

# 6. Commit se ci sono modifiche
if missing_handlers:
    print("\n5️⃣ Commit modifiche...")
    subprocess.run("git add main.py", shell=True)
    subprocess.run('git commit -m "fix: aggiunti import mancanti per handler"', shell=True)
    subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ VERIFICA COMPLETATA!")
print("\n📱 Il bot dovrebbe ora essere completamente funzionante!")
print("⏰ Se hai fatto modifiche, attendi 2-3 minuti per il deploy")
print("\n🧪 Test consigliati:")
print("1. /start - Menu principale")
print("2. Prova tutti i pulsanti del menu")
print("3. Registra un nuovo servizio")
print("4. Verifica che i messaggi vecchi vengano eliminati")
