#!/usr/bin/env python3
import subprocess

print("🔧 AGGIORNAMENTO MAIN.PY")
print("=" * 50)

# Leggi il main.py esistente
with open('main.py', 'r') as f:
    content = f.read()

# Trova la sezione dove vengono aggiunti gli handler
handler_section_start = content.find("# Command handlers")
handler_section_end = content.find("# Run the bot")

if handler_section_start == -1 or handler_section_end == -1:
    print("❌ Non riesco a trovare la sezione handler")
    exit(1)

# Nuovo codice per la registrazione handler
new_handler_code = '''    # Registra tutti gli handler usando il manager
    from utils.handler_manager import HandlerManager
    
    handler_manager = HandlerManager(application)
    handler_manager.register_all_handlers()
    
    logger.info("✅ Tutti gli handler registrati tramite HandlerManager")
    
'''

# Sostituisci la sezione
new_content = (
    content[:handler_section_start] + 
    new_handler_code + 
    content[handler_section_end:]
)

# Salva
with open('main.py', 'w') as f:
    f.write(new_content)

print("✅ main.py aggiornato")

# Commit
subprocess.run("git add main.py", shell=True)
subprocess.run('git commit -m "refactor: main.py ora usa HandlerManager per registrazione centralizzata"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n✅ main.py aggiornato con successo!")

import os
os.remove(__file__)
