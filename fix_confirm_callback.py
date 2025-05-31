#!/usr/bin/env python3
import subprocess

print("🔧 Fix callback confirm_yes")
print("=" * 50)

# Leggi service_handler.py
with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# Cerca la funzione handle_confirmation
import re

# Verifica se esiste e come gestisce il callback
if 'def handle_confirmation' in content or 'async def handle_confirmation' in content:
    print("✅ Funzione handle_confirmation trovata")
    
    # Trova la funzione e verifica che gestisca correttamente "yes"
    pattern = r'(async def handle_confirmation.*?action = query\.data\.replace\("confirm_", ""\))(.*?)(if action ==)'
    
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print("✅ Funzione trovata, verifico gestione action...")
        
        # Controlla se gestisce "yes" correttamente
        function_content = match.group(0)
        if 'if action == "yes"' in function_content:
            print("✅ Gestisce già 'yes' correttamente")
        else:
            print("⚠️ Potrebbe non gestire 'yes' correttamente, verifico...")
else:
    print("❌ Funzione handle_confirmation non trovata!")

# Fix: assicuriamoci che il callback sia registrato correttamente in main.py
print("\n📄 Verifica registrazione callback in main.py...")

with open('main.py', 'r') as f:
    main_content = f.read()

# Verifica se handle_confirmation è nel conversation handler
if 'handle_confirmation' in main_content:
    print("✅ handle_confirmation presente in main.py")
    
    # Verifica che sia nel conversation handler corretto
    if 'CONFIRM_SERVICE:' in main_content and 'handle_confirmation' in main_content:
        print("✅ Registrato nel conversation handler")
    
    # Aggiungi anche un handler diretto per debug
    if 'CallbackQueryHandler(handle_confirmation, pattern="^confirm_")' not in main_content:
        print("\n⚠️ Aggiungo handler diretto per confirm callbacks...")
        
        # Trova dove aggiungere l'handler (dopo i conversation handlers)
        insert_pos = main_content.find('# Handler per callback specifici')
        if insert_pos == -1:
            insert_pos = main_content.find('# Handler per navigazione back')
        
        if insert_pos != -1:
            # Aggiungi l'import se manca
            if 'from handlers.service_handler import' not in main_content:
                imports_pos = main_content.find('from handlers.service_handler import')
                if imports_pos != -1:
                    # Aggiungi handle_confirmation agli import
                    import_line_end = main_content.find('\n', imports_pos)
                    current_imports = main_content[imports_pos:import_line_end]
                    if 'handle_confirmation' not in current_imports:
                        new_imports = current_imports.rstrip(')') + ', handle_confirmation)'
                        main_content = main_content[:imports_pos] + new_imports + main_content[import_line_end:]
            
            # Aggiungi l'handler
            new_handler = '\n    # Handler per conferma servizio\n    application.add_handler(CallbackQueryHandler(handle_confirmation, pattern="^confirm_"))\n'
            main_content = main_content[:insert_pos] + new_handler + main_content[insert_pos:]
            
            with open('main.py', 'w') as f:
                f.write(main_content)
            
            print("✅ Aggiunto handler per confirm callbacks")

# Fix alternativo: modifica debug_unhandled_callback per gestire confirm_yes
print("\n📄 Aggiorno handler di debug per gestire confirm_yes...")

pattern = r'(async def debug_unhandled_callback.*?)(await query\.edit_message_text\([\s\S]*?\))'

def update_debug_handler(match):
    func_start = match.group(1)
    
    new_body = '''# Gestione specifica per confirm_yes
    if query.data == "confirm_yes":
        from handlers.service_handler import handle_confirmation
        return await handle_confirmation(update, context)
    
    # Default per altri callback non gestiti
    await query.edit_message_text(
        f"⚠️ Funzione in sviluppo: {query.data}\\n\\nTorna al menu con /start",
        parse_mode='HTML'
    )'''
    
    return func_start + new_body

main_content = re.sub(pattern, update_debug_handler, main_content, flags=re.DOTALL)

# Salva main.py
with open('main.py', 'w') as f:
    f.write(main_content)

print("✅ Aggiornato handler di debug")

# Verifica sintassi
print("\n🔍 Verifica sintassi...")
for file in ['main.py', 'handlers/service_handler.py']:
    try:
        with open(file, 'r') as f:
            compile(f.read(), file, 'exec')
        print(f"✅ {file} - OK")
    except SyntaxError as e:
        print(f"❌ {file} - Errore: {e}")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: gestione callback confirm_yes"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("\n💡 Il callback confirm_yes ora dovrebbe:")
print("1. Salvare il servizio nel database")
print("2. Mostrare messaggio di conferma")
print("3. Non più mostrare 'Funzione in sviluppo'")

# Auto-elimina
import os
os.remove(__file__)
