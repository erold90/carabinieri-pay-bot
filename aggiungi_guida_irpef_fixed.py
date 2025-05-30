#!/usr/bin/env python3
import subprocess
import os
import re

print("📊 AGGIUNTA GUIDA SELEZIONE IRPEF")
print("=" * 50)

# 1. Modifica settings_handler.py
print("\n1️⃣ Modifica settings_handler.py...")

with open('handlers/settings_handler.py', 'r') as f:
    content = f.read()

# Trova la funzione show_irpef_selection e modificala
new_show_irpef = '''async def show_irpef_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show IRPEF selection with guide"""
    text = "💰 <b>SELEZIONA L'ALIQUOTA IRPEF</b>\\n\\n"
    text += "📊 <b>GUIDA SCAGLIONI IRPEF 2024:</b>\\n"
    text += "• Fino a €15.000 di reddito: <b>23%</b>\\n"
    text += "• Da €15.001 a €28.000: <b>25%</b>\\n"
    text += "• Da €28.001 a €50.000: <b>35%</b>\\n"
    text += "• Oltre €50.000: <b>43%</b>\\n\\n"
    text += "💡 <i>Puoi verificare la tua aliquota sul cedolino stipendio</i>\\n\\n"
    text += "Seleziona la tua aliquota attuale:"
    
    await update.callback_query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=get_irpef_keyboard()
    )'''

# Sostituisci la funzione
if 'async def show_irpef_selection' in content:
    start = content.find('async def show_irpef_selection')
    end = content.find('\n\nasync def', start + 1)
    if end == -1:
        end = content.find('\n\n# ', start + 1)
    if end > start:
        content = content[:start] + new_show_irpef.strip() + '\n' + content[end:]
else:
    # Se non esiste, aggiungila prima di update_irpef
    pos = content.find('async def update_irpef')
    if pos > 0:
        content = content[:pos] + new_show_irpef + '\n\n' + content[pos:]

with open('handlers/settings_handler.py', 'w') as f:
    f.write(content)

print("✅ settings_handler.py aggiornato")

# 2. Modifica anche setup_handler.py se esiste
if os.path.exists('handlers/setup_handler.py'):
    print("\n2️⃣ Modifica setup_handler.py...")
    
    with open('handlers/setup_handler.py', 'r') as f:
        setup_content = f.read()
    
    # Trova la parte dove si seleziona IRPEF nel setup
    new_setup_irpef_text = '''    text = f"✅ Comando: <b>{command_name}</b>\\n\\n"
    text += "💰 <b>Passo 3 di 4: Aliquota IRPEF</b>\\n\\n"
    text += "📊 <b>GUIDA SCAGLIONI IRPEF 2024:</b>\\n"
    text += "• Fino a €15.000 di reddito: <b>23%</b>\\n"
    text += "• Da €15.001 a €28.000: <b>25%</b>\\n"
    text += "• Da €28.001 a €50.000: <b>35%</b>\\n"
    text += "• Oltre €50.000: <b>43%</b>\\n\\n"
    text += "💡 <i>Puoi verificare la tua aliquota sul cedolino stipendio</i>\\n\\n"
    text += "Seleziona la tua aliquota attuale:"'''
    
    # Sostituisci il testo nella funzione setup_command
    pattern = r'text = f"✅ Comando:.*?Seleziona la tua aliquota IRPEF attuale:"'
    setup_content = re.sub(pattern, new_setup_irpef_text, setup_content, flags=re.DOTALL)
    
    with open('handlers/setup_handler.py', 'w') as f:
        f.write(setup_content)
    
    print("✅ setup_handler.py aggiornato")

# 3. Aggiorna anche utils/keyboards.py per migliorare i pulsanti IRPEF
print("\n3️⃣ Modifica keyboards.py...")

with open('utils/keyboards.py', 'r') as f:
    keyboards_content = f.read()

# Trova e modifica get_irpef_keyboard
new_irpef_keyboard = '''def get_irpef_keyboard():
    """Get IRPEF rate keyboard with descriptions"""
    keyboard = [
        [
            InlineKeyboardButton("23% (fino a 15k€)", callback_data="irpef_23"),
            InlineKeyboardButton("25% (15-28k€)", callback_data="irpef_25")
        ],
        [
            InlineKeyboardButton("27% (media)", callback_data="irpef_27"),
            InlineKeyboardButton("35% (28-50k€)", callback_data="irpef_35")
        ],
        [
            InlineKeyboardButton("43% (oltre 50k€)", callback_data="irpef_43")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)'''

# Sostituisci la funzione
if 'def get_irpef_keyboard' in keyboards_content:
    start = keyboards_content.find('def get_irpef_keyboard')
    end = keyboards_content.find('\n\ndef ', start + 1)
    if end == -1:
        end = keyboards_content.find('\n\nclass ', start + 1)
    if end > start:
        keyboards_content = keyboards_content[:start] + new_irpef_keyboard.strip() + '\n' + keyboards_content[end:]
else:
    # Se non esiste, aggiungila
    keyboards_content += '\n\n' + new_irpef_keyboard

with open('utils/keyboards.py', 'w') as f:
    f.write(keyboards_content)

print("✅ keyboards.py aggiornato")

# 4. Verifica sintassi
print("\n4️⃣ Verifica sintassi...")

files_to_check = ['handlers/settings_handler.py', 'utils/keyboards.py']
if os.path.exists('handlers/setup_handler.py'):
    files_to_check.append('handlers/setup_handler.py')

all_ok = True
for file in files_to_check:
    result = subprocess.run(['python3', '-m', 'py_compile', file], capture_output=True)
    if result.returncode == 0:
        print(f"✅ {file}: OK")
    else:
        print(f"❌ {file}: Errore")
        print(result.stderr.decode())
        all_ok = False

# 5. Commit e push
if all_ok:
    print("\n5️⃣ Commit e push...")
    files_to_add = ' '.join(files_to_check)
    subprocess.run(f"git add {files_to_add}", shell=True)
    subprocess.run('git commit -m "feat: aggiunta guida scaglioni IRPEF con descrizioni dettagliate"', shell=True)
    subprocess.run("git push origin main", shell=True)
    print("✅ Push completato")

print("\n" + "=" * 50)
print("✅ GUIDA IRPEF IMPLEMENTATA!")
print("\n📊 Modifiche apportate:")
print("1. Aggiunta tabella scaglioni IRPEF 2024")
print("2. Pulsanti con descrizione fascia di reddito")
print("3. Suggerimento di verificare sul cedolino")
print("\n💡 Ora quando l'utente deve selezionare l'IRPEF vedrà:")
print("- Tabella completa degli scaglioni")
print("- Pulsanti chiari con fascia di reddito")
print("- Guida per scegliere correttamente")
print("\n⏰ Attendi 2-3 minuti per il deploy")
