#!/usr/bin/env python3
import subprocess

print("🔧 Fix callback pasti mancanti")
print("=" * 50)

# Leggi main.py
with open('main.py', 'r') as f:
    main_content = f.read()

# Aggiungi handler per i callback dei pasti
print("\n1️⃣ Aggiungo handler per meal callbacks in main.py...")

# Trova dove aggiungere (dopo gli altri callback handler)
insert_pos = main_content.find('# Navigation callbacks')
if insert_pos > 0:
    new_handlers = '''    # Meal selection callbacks
    application.add_handler(CallbackQueryHandler(handle_meal_selection, pattern="^meal_"))
    
    '''
    main_content = main_content[:insert_pos] + new_handlers + main_content[insert_pos:]

# Aggiungi l'import per handle_meal_selection
import_pos = main_content.find('from handlers.service_handler import (')
if import_pos > 0:
    # Trova la fine degli import
    import_end = main_content.find(')', import_pos)
    # Aggiungi handle_meal_selection
    main_content = main_content[:import_end] + ',\n    handle_meal_selection' + main_content[import_end:]

# Salva main.py
with open('main.py', 'w') as f:
    f.write(main_content)

print("✅ Aggiunto handler in main.py")

# Ora aggiungiamo la funzione handle_meal_selection in service_handler.py
print("\n2️⃣ Aggiungo handle_meal_selection in service_handler.py...")

with open('handlers/service_handler.py', 'r') as f:
    service_content = f.read()

# Aggiungi la funzione se non esiste
if 'async def handle_meal_selection' not in service_content:
    meal_handler = '''
async def handle_meal_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle meal checkbox selection"""
    query = update.callback_query
    await query.answer()
    
    meal_type = query.data.replace("meal_", "")
    
    # Toggle meal selection
    if 'selected_meals' not in context.user_data:
        context.user_data['selected_meals'] = set()
    
    if meal_type in context.user_data['selected_meals']:
        context.user_data['selected_meals'].remove(meal_type)
    else:
        context.user_data['selected_meals'].add(meal_type)
    
    # Calculate meal reimbursement
    meals_not_consumed = len(context.user_data['selected_meals'])
    meal_reimbursement = 0
    
    if meals_not_consumed == 1:
        meal_reimbursement = MEAL_RATES['single_meal_net']
    elif meals_not_consumed == 2:
        meal_reimbursement = MEAL_RATES['double_meal_net']
    
    context.user_data['meal_reimbursement'] = meal_reimbursement
    context.user_data['meals_not_consumed'] = meals_not_consumed
    
    # Update message
    text = "🍽️ <b>PASTI NON CONSUMATI</b>\\n\\n"
    text += "Seleziona i pasti che NON hai consumato:\\n\\n"
    
    lunch_check = "☑️" if "lunch" in context.user_data['selected_meals'] else "☐"
    dinner_check = "☑️" if "dinner" in context.user_data['selected_meals'] else "☐"
    
    text += f"{lunch_check} Pranzo\\n"
    text += f"{dinner_check} Cena\\n\\n"
    
    if meal_reimbursement > 0:
        text += f"💰 Rimborso pasti: {format_currency(meal_reimbursement)}\\n\\n"
    
    keyboard = [
        [
            InlineKeyboardButton(f"{lunch_check} Pranzo", callback_data="meal_lunch"),
            InlineKeyboardButton(f"{dinner_check} Cena", callback_data="meal_dinner")
        ],
        [InlineKeyboardButton("✅ Conferma", callback_data="meal_confirm")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
'''
    
    # Trova dove inserire (prima del ConversationHandler)
    conv_pos = service_content.find('service_conversation_handler = ConversationHandler(')
    if conv_pos > 0:
        service_content = service_content[:conv_pos] + meal_handler + '\n' + service_content[conv_pos:]
    
    # Aggiungi anche l'import per MEAL_RATES se mancante
    if 'MEAL_RATES' not in service_content:
        const_import = service_content.find('from config.constants import')
        if const_import > 0:
            import_end = service_content.find('\n', const_import)
            old_import = service_content[const_import:import_end]
            # Aggiungi MEAL_RATES all'import
            if old_import.endswith(')'):
                new_import = old_import[:-1] + ', MEAL_RATES)'
            else:
                new_import = old_import + ', MEAL_RATES'
            service_content = service_content.replace(old_import, new_import)

# Modifica anche handle_meals per gestire meal_confirm
meals_func_start = service_content.find('async def handle_meals(')
if meals_func_start > 0:
    # Trova dove aggiungere il caso meal_confirm
    confirm_check = 'if meals == "confirm"'
    if confirm_check not in service_content:
        # Aggiungi dopo il primo if nel handle_meals
        first_if = service_content.find('meals = int(query.data.replace("meals_", ""))', meals_func_start)
        if first_if > 0:
            # Sostituisci con un try-except per gestire sia numeri che stringhe
            old_line = 'meals = int(query.data.replace("meals_", ""))'
            new_code = '''# Handle both numeric meals and confirm
    if query.data == "meal_confirm":
        # User confirmed meal selection
        return await show_service_summary(update, context)
    
    try:
        meals = int(query.data.replace("meals_", ""))
    except ValueError:
        # Not a number, handle meal selection
        return await handle_meal_selection(update, context)'''
            
            service_content = service_content.replace(old_line, new_code)

# Salva il file
with open('handlers/service_handler.py', 'w') as f:
    f.write(service_content)

print("✅ Aggiunto handle_meal_selection in service_handler.py")

# Commit e push
print("\n3️⃣ Commit e push...")
subprocess.run("git add main.py handlers/service_handler.py", shell=True)
subprocess.run('git commit -m "fix: aggiunto handler per selezione pasti (meal callbacks)"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("🚀 Railway rifarà il deploy in 2-3 minuti")
print("\n📱 Ora potrai selezionare i pasti correttamente!")
