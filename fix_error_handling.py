#!/usr/bin/env python3
import subprocess
import os

print("🔧 FIX GESTIONE ERRORI")
print("=" * 50)

# Modifica start_handler.py per aggiungere try/catch
with open('handlers/start_handler.py', 'r') as f:
    content = f.read()

# Trova start_command e aggiungi try/except
lines = content.split('\n')
modified = False

for i, line in enumerate(lines):
    if 'async def start_command(update: Update' in line:
        # Trova dove inizia il codice della funzione
        j = i + 1
        while j < len(lines) and (lines[j].strip() == '' or '"""' in lines[j] or lines[j].strip().startswith('#')):
            j += 1
        
        # Se non c'è già un try
        if j < len(lines) and not lines[j].strip().startswith('try:'):
            # Inserisci try
            indent = '    '
            lines.insert(j, f'{indent}try:')
            
            # Indenta tutto il resto della funzione
            k = j + 1
            while k < len(lines) and (lines[k].startswith(indent) or lines[k].strip() == ''):
                if lines[k].strip():
                    lines[k] = '    ' + lines[k]
                k += 1
            
            # Aggiungi except alla fine
            lines.insert(k, f'{indent}except Exception as e:')
            lines.insert(k+1, f'{indent*2}logger.error(f"Errore in start_command: {{e}}", exc_info=True)')
            lines.insert(k+2, f'{indent*2}if update.message:')
            lines.insert(k+3, f'{indent*3}await update.message.reply_text("❌ Si è verificato un errore. Riprova con /start")')
            
            modified = True
            print("✅ Aggiunto try/except in start_command")
        break

if modified:
    content = '\n'.join(lines)
    with open('handlers/start_handler.py', 'w') as f:
        f.write(content)

# Aggiungi anche error handler globale in main.py
print("\n📝 Aggiungo error handler globale...")
with open('main.py', 'r') as f:
    main_content = f.read()

# Cerca la funzione error_handler
if 'async def error_handler(update' in main_content:
    print("✅ Error handler già presente")
else:
    # Modifica l'error handler esistente o aggiungine uno nuovo
    lines = main_content.split('\n')
    
    # Trova dove aggiungere (prima di main)
    for i, line in enumerate(lines):
        if 'def main():' in line:
            error_handler_code = '''
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log degli errori causati dagli Updates."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Prova a inviare messaggio di errore all'utente
    try:
        if update and hasattr(update, 'effective_message') and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Si è verificato un errore. Riprova con /start"
            )
    except:
        pass
'''
            lines.insert(i-1, error_handler_code)
            print("✅ Aggiunto error handler migliorato")
            break
    
    main_content = '\n'.join(lines)
    with open('main.py', 'w') as f:
        f.write(main_content)

# Verifica che ci sia l'import corretto per logger
print("\n🔍 Verifica imports...")
for file in ['main.py', 'handlers/start_handler.py']:
    with open(file, 'r') as f:
        content = f.read()
    
    if 'import logging' not in content:
        lines = content.split('\n')
        # Aggiungi dopo i primi import
        for i, line in enumerate(lines):
            if 'import' in line:
                lines.insert(i+1, 'import logging')
                lines.insert(i+2, 'logger = logging.getLogger(__name__)')
                break
        
        with open(file, 'w') as f:
            f.write('\n'.join(lines))
        print(f"✅ Aggiunto logging in {file}")

# Verifica sintassi
print("\n🔍 Verifica sintassi...")
for file in ['main.py', 'handlers/start_handler.py']:
    result = subprocess.run(['python3', '-m', 'py_compile', file], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ {file} OK")
    else:
        print(f"❌ {file}: {result.stderr}")

# Commit e push
print("\n📤 Push fix...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: aggiunta gestione errori dettagliata per debug"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ GESTIONE ERRORI MIGLIORATA!")
print("\nOra quando c'è un errore vedrai:")
print("1. L'errore completo nei log")
print("2. Un messaggio di errore user-friendly su Telegram")
print("\n🔍 Controlla i log di Railway per vedere l'errore dettagliato!")

os.remove(__file__)
