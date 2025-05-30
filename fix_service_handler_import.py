#!/usr/bin/env python3
import re

print("🔧 Fix import error in service_handler.py")

# Leggi il file
with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# Trova la sezione degli import
import_section_end = content.find('async def new_service_command')

# Aggiungi l'import mancante se non c'è già
if 'from handlers.start_handler import start_command' not in content:
    # Trova l'ultimo import
    last_import = content[:import_section_end].rfind('from')
    last_import_end = content.find('\n', last_import)
    
    # Aggiungi il nuovo import
    new_import = '\nfrom handlers.start_handler import start_command\n'
    content = content[:last_import_end] + new_import + content[last_import_end:]
    print("✅ Aggiunto import: from handlers.start_handler import start_command")
else:
    print("ℹ️  Import già presente")

# Scrivi il file aggiornato
with open('handlers/service_handler.py', 'w') as f:
    f.write(content)

print("✅ File handlers/service_handler.py aggiornato!")
print("\nOra committa e pusha le modifiche:")
print("python3 git_update.py")
