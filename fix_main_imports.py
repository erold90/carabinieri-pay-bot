#!/usr/bin/env python3
import subprocess

print("🔧 Fix imports in main.py")
print("=" * 50)

# Leggi main.py
with open('main.py', 'r') as f:
    content = f.read()

# Trova la sezione degli import di telegram
import_line = content.find('from telegram.ext import')
if import_line != -1:
    # Trova la fine della riga
    line_end = content.find('\n', import_line)
    current_imports = content[import_line:line_end]
    
    # Aggiungi ContextTypes se mancante
    if 'ContextTypes' not in current_imports:
        # Sostituisci la riga con gli import completi
        new_imports = 'from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler, ContextTypes'
        content = content[:import_line] + new_imports + content[line_end:]
        print("✅ Aggiunto ContextTypes agli import")

# Assicurati che Update sia importato
if 'from telegram import Update' not in content:
    # Aggiungi dopo gli import iniziali
    first_import = content.find('import ')
    line_end = content.find('\n', first_import)
    content = content[:line_end] + '\nfrom telegram import Update' + content[line_end:]
    print("✅ Aggiunto import Update")

# Salva il file
with open('main.py', 'w') as f:
    f.write(content)

print("✅ Import corretti!")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add main.py", shell=True)
subprocess.run('git commit -m "fix: aggiunto ContextTypes agli import in main.py"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("⏰ Il bot ripartirà tra 1-2 minuti")
