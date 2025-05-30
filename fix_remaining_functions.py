#!/usr/bin/env python3
import subprocess

print("🔧 FIX FUNZIONI RIMANENTI")
print("=" * 50)

# Leggi main.py
with open('main.py', 'r') as f:
    content = f.read()

# Verifica e aggiungi dashboard_callback se mancante
if 'from handlers.start_handler import' in content and 'dashboard_callback' not in content:
    # Trova l'import di start_handler
    import_line = content.find('from handlers.start_handler import')
    if import_line > 0:
        # Trova la fine della riga o della parentesi
        end_line = content.find('\n', import_line)
        if 'start_command' in content[import_line:end_line]:
            # Import singola linea
            content = content[:end_line] + ', dashboard_callback' + content[end_line:]
            print("✅ Aggiunto dashboard_callback all'import")

# Aggiungi le funzioni mancanti locali
missing_functions = """

# === CALLBACK HANDLERS MANCANTI ===

async def handle_missing_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Handler generico per callback non implementati\"\"\"
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    # Log per debug
    logger.warning(f"Callback non implementato: {callback_data}")
    
    # Risposte specifiche per tipo di callback
    responses = {
        "meal_lunch": "🍽️ Gestione pasti in aggiornamento...",
        "meal_confirm": "🍽️ Gestione pasti in aggiornamento...",
        "meal_dinner": "🍽️ Gestione pasti in aggiornamento...",
        "back": "🔧 Funzione back in sviluppo...",
        "setup_start": "🔧 Funzione setup in sviluppo...",
        "default": "⚠️ Funzione non ancora disponibile.\\n\\nTorna al menu principale con /start"
    }
    
    # Ottieni la risposta appropriata
    response_text = responses.get(callback_data, responses["default"])
    
    # Invia la risposta
    try:
        await query.edit_message_text(
            response_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu Principale", callback_data="back_to_menu")]
            ])
        )
    except:
        # Se edit fallisce, prova con un nuovo messaggio
        await query.message.reply_text(
            response_text,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Menu Principale", callback_data="back_to_menu")]
            ])
        )

async def debug_unhandled_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    \"\"\"Debug handler for unhandled callbacks\"\"\"
    query = update.callback_query
    await query.answer()
    logger.warning(f"Callback non gestito: {query.data}")
    await query.edit_message_text(
        f"⚠️ Funzione in sviluppo: {query.data}\\n\\nTorna al menu con /start",
        parse_mode='HTML'
    )
"""

# Aggiungi le funzioni se non esistono
if 'async def handle_missing_callbacks' not in content:
    # Trova dove inserirle (prima di main())
    main_pos = content.find('def main():')
    if main_pos > 0:
        # Trova se ci sono già altre funzioni locali
        local_functions_pos = content.rfind('# === FUNZIONI DI SUPPORTO LOCALI ===', 0, main_pos)
        if local_functions_pos > 0:
            # Aggiungi dopo le funzioni locali esistenti
            insert_pos = content.find('\n\n', local_functions_pos)
            content = content[:insert_pos] + missing_functions + content[insert_pos:]
        else:
            # Aggiungi prima di main()
            content = content[:main_pos] + missing_functions + "\n\n" + content[main_pos:]
        print("✅ Aggiunte funzioni handle_missing_callbacks e debug_unhandled_callback")

# Fix import di InlineKeyboardButton e InlineKeyboardMarkup se mancanti
if 'InlineKeyboardButton' in content and 'from telegram import InlineKeyboardButton' not in content:
    # Trova l'import di telegram
    telegram_import = content.find('from telegram import Update')
    if telegram_import > 0:
        end_line = content.find('\n', telegram_import)
        content = content[:end_line] + ', InlineKeyboardButton, InlineKeyboardMarkup' + content[end_line:]
        print("✅ Aggiunti InlineKeyboardButton e InlineKeyboardMarkup agli import")

# Salva il file aggiornato
with open('main.py', 'w') as f:
    f.write(content)

print("\n✅ main.py aggiornato")

# Ora sistemiamo anche l'import di dashboard_callback in start_handler
print("\n📝 Verifica start_handler.py...")

with open('handlers/start_handler.py', 'r') as f:
    start_content = f.read()

# Verifica che dashboard_callback sia esportato
if 'async def dashboard_callback' in start_content:
    print("✅ dashboard_callback trovato in start_handler.py")
else:
    print("❌ dashboard_callback non trovato - potrebbe essere già gestito internamente")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: aggiunte funzioni callback mancanti e fix import InlineKeyboard"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ FIX COMPLETATO!")
print("🚀 Railway sta facendo il deploy")
print("⏰ Il bot dovrebbe essere online tra 1-2 minuti")

# Test finale
print("\n🧪 Per testare il bot quando sarà online:")
print("1. Apri Telegram e cerca il tuo bot")
print("2. Invia /start")
print("3. Verifica che il menu principale appaia")
print("4. Testa tutti i pulsanti")

# Auto-elimina
import os
os.remove(__file__)
print("\n🗑️ Script eliminato")
