#!/usr/bin/env python3
import subprocess

print("🔧 Fix main.py - rimozione handler non definiti")
print("=" * 50)

# Leggi main.py
with open('main.py', 'r') as f:
    lines = f.readlines()

# Rimuovi le righe problematiche
new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
        
    # Salta le righe con handler non definiti
    if 'handle_back_callbacks' in line:
        continue
    if 'handle_setup_callbacks' in line:
        continue
    if 'handle_settings_text_input' in line:
        # Salta anche le prossime 4 righe (il blocco MessageHandler)
        skip_count = 4
        continue
        
    new_lines.append(line)

# Salva il file corretto
with open('main.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Rimossi handler non definiti")

# Verifica che settings_handler sia importato correttamente
content = ''.join(new_lines)

# Se settings_handler_complete è importato, cambialo in settings_handler
if 'from handlers.settings_handler_complete import' in content:
    content = content.replace(
        'from handlers.settings_handler_complete import',
        'from handlers.settings_handler import'
    )
    with open('main.py', 'w') as f:
        f.write(content)
    print("✅ Corretto import settings_handler")

# Assicurati che handle_text_input sia gestito correttamente
if 'handle_text_input' in content and 'from handlers.settings_handler import' in content:
    # Aggiungi un MessageHandler generico per gestire l'input di testo
    add_handler = '''
    # Handler for text input in conversations
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_input
    ))
    '''
    
    # Trova dove aggiungere (prima di run_polling)
    run_polling_pos = content.find('application.run_polling()')
    if run_polling_pos > 0 and 'MessageHandler' not in content[run_polling_pos-200:run_polling_pos]:
        content = content[:run_polling_pos] + add_handler + '\n    ' + content[run_polling_pos:]
        with open('main.py', 'w') as f:
            f.write(content)
        print("✅ Aggiunto handler per input testo")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add main.py", shell=True)
subprocess.run('git commit -m "fix: rimossi handler non definiti da main.py"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("⏰ Il bot dovrebbe ripartire correttamente ora")
