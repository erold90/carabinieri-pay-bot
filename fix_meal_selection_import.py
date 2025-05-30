#!/usr/bin/env python3
import subprocess

print("🔧 FIX IMPORT handle_meal_selection")
print("=" * 50)

# 1. Rimuovi l'import non esistente da main.py
print("\n1️⃣ Rimozione import non esistente...")

with open('main.py', 'r') as f:
    content = f.read()

# Rimuovi handle_meal_selection dall'import
content = content.replace('handle_meal_selection,\n', '')
content = content.replace(',\n    handle_meal_selection', '')
content = content.replace(', handle_meal_selection', '')
content = content.replace('handle_meal_selection, ', '')

# Rimuovi anche eventuali handler che lo usano
lines = content.split('\n')
filtered_lines = []
for line in lines:
    if 'handle_meal_selection' not in line:
        filtered_lines.append(line)
    else:
        print(f"Rimossa riga: {line.strip()}")

content = '\n'.join(filtered_lines)

# 2. Aggiungi per_message=False al ConversationHandler per evitare il warning
print("\n2️⃣ Fix warning ConversationHandler...")

with open('handlers/service_handler.py', 'r') as f:
    service_content = f.read()

# Trova il ConversationHandler e aggiungi per_message=False
if 'per_message=False' not in service_content:
    service_content = service_content.replace(
        'fallbacks=[CommandHandler("start", start_command)]',
        'fallbacks=[CommandHandler("start", start_command)],\n    per_message=False'
    )

# 3. Verifica che handle_meals esista e sia corretto
print("\n3️⃣ Verifica handle_meals...")

if 'async def handle_meals' not in service_content:
    print("⚠️ handle_meals non trovato, lo aggiungo...")
    
    # Aggiungi la funzione handle_meals prima del ConversationHandler
    handle_meals_func = '''
async def handle_meals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle meal selection"""
    query = update.callback_query
    await query.answer()
    
    meals = int(query.data.replace("meals_", ""))
    context.user_data['meals_consumed'] = meals
    
    # Vai direttamente al riepilogo
    return await show_service_summary(update, context)
'''
    
    # Inserisci prima del ConversationHandler
    conv_pos = service_content.find('service_conversation_handler = ConversationHandler')
    if conv_pos > 0:
        service_content = service_content[:conv_pos] + handle_meals_func + '\n\n' + service_content[conv_pos:]

# 4. Salva i file
print("\n4️⃣ Salvataggio file...")

with open('main.py', 'w') as f:
    f.write(content)
print("✅ main.py aggiornato")

with open('handlers/service_handler.py', 'w') as f:
    f.write(service_content)
print("✅ service_handler.py aggiornato")

# 5. Verifica sintassi
print("\n5️⃣ Verifica sintassi...")

for file in ['main.py', 'handlers/service_handler.py']:
    result = subprocess.run(['python3', '-m', 'py_compile', file], capture_output=True)
    if result.returncode == 0:
        print(f"✅ {file}: sintassi OK")
    else:
        print(f"❌ {file}: errore sintassi")
        print(result.stderr.decode())

# 6. Commit e push
print("\n6️⃣ Commit e push...")
subprocess.run("git add main.py handlers/service_handler.py", shell=True)
subprocess.run('git commit -m "fix: rimosso import handle_meal_selection non esistente e aggiunto per_message=False"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ FIX COMPLETATO!")
print("\n⏰ Railway rifarà il deploy in 1-2 minuti")
print("📊 Monitora con: railway logs -f")
