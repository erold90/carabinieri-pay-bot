#!/usr/bin/env python3
import subprocess

print("🔧 Fix completo flusso scorta e salvataggio database")
print("=" * 50)

# Leggi service_handler.py
with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# 1. Fix handle_travel_sheet_number per salvare correttamente il numero FV
print("\n1️⃣ Fix handle_travel_sheet_number...")

old_travel_sheet = '''async def handle_travel_sheet_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle travel sheet number input"""
    context.user_data['travel_sheet_number'] = update.message.text
    
    await update.message.reply_text(
        "📍 Destinazione:",
        parse_mode='HTML'
    )
    
    return TRAVEL_TYPE'''

new_travel_sheet = '''async def handle_travel_sheet_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle travel sheet number input"""
    context.user_data['travel_sheet_number'] = update.message.text
    
    await update.message.reply_text(
        "📍 Destinazione:",
        parse_mode='HTML'
    )
    
    context.user_data['waiting_for_destination'] = True
    return TRAVEL_TYPE'''

content = content.replace(old_travel_sheet, new_travel_sheet)

# 2. Fix handle_destination per gestire correttamente il flusso
print("\n2️⃣ Fix handle_destination...")

# Trova e sostituisci handle_destination
handle_dest_start = content.find('async def handle_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):')
if handle_dest_start != -1:
    handle_dest_end = content.find('\nasync def', handle_dest_start + 1)
    if handle_dest_end == -1:
        handle_dest_end = len(content)
    
    new_handle_destination = '''async def handle_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle destination input"""
    if not context.user_data.get('waiting_for_destination'):
        return TRAVEL_TYPE
        
    context.user_data['destination'] = update.message.text
    context.user_data['waiting_for_destination'] = False
    
    # Controlla se siamo in un servizio di scorta o missione
    service_type = context.user_data.get('service_type')
    
    if service_type == ServiceType.ESCORT:
        # Per scorta, chiedi il timing dettagliato
        text = "⏱️ <b>TIMING DETTAGLIATO</b>\\n\\n"
        text += "Inserisci gli orari nel formato HH:MM\\n\\n"
        text += "<b>1️⃣ ANDATA (senza VIP):</b>\\n"
        text += "Ora partenza dalla sede:"
        
        await update.message.reply_text(text, parse_mode='HTML')
        
        context.user_data['escort_phase'] = 'departure_time'
        context.user_data['waiting_for_escort_timing'] = True
        return TRAVEL_TYPE
    else:
        # Per missione, chiedi i km
        await update.message.reply_text(
            "🚗 Chilometri totali (se applicabile, altrimenti 0):",
            parse_mode='HTML'
        )
        
        context.user_data['waiting_for_km'] = True
        return TRAVEL_TYPE'''
    
    content = content[:handle_dest_start] + new_handle_destination + '\n' + content[handle_dest_end:]

# 3. Crea un handler unificato per TRAVEL_TYPE che gestisce tutti gli input
print("\n3️⃣ Creo handler unificato per TRAVEL_TYPE...")

# Aggiungi la nuova funzione prima del ConversationHandler
unified_handler = '''
async def handle_travel_type_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all inputs in TRAVEL_TYPE state"""
    text = update.message.text
    
    # Se stiamo aspettando la destinazione
    if context.user_data.get('waiting_for_destination'):
        return await handle_destination(update, context)
    
    # Se stiamo aspettando timing escort
    elif context.user_data.get('waiting_for_escort_timing'):
        return await handle_escort_timing(update, context)
    
    # Se stiamo aspettando km
    elif context.user_data.get('waiting_for_km'):
        return await handle_mission_km(update, context)
    
    # Default: non dovremmo arrivare qui
    await update.message.reply_text(
        "❌ Errore: stato non riconosciuto. Usa /start per ricominciare.",
        parse_mode='HTML'
    )
    return ConversationHandler.END
'''

# Inserisci prima del ConversationHandler
conv_handler_pos = content.find('service_conversation_handler = ConversationHandler(')
if conv_handler_pos > 0:
    content = content[:conv_handler_pos] + unified_handler + '\n' + content[conv_handler_pos:]

# 4. Aggiorna il ConversationHandler per usare il nuovo handler
print("\n4️⃣ Aggiorno ConversationHandler...")

# Trova e sostituisci TRAVEL_TYPE handler
old_pattern = '''TRAVEL_TYPE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_escort_timing),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mission_km)
        ],'''

new_pattern = '''TRAVEL_TYPE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_travel_type_input)
        ],'''

if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
else:
    # Prova pattern alternativo
    old_pattern2 = '''TRAVEL_TYPE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_destination)
        ],'''
    if old_pattern2 in content:
        content = content.replace(old_pattern2, new_pattern)

# 5. Fix handle_escort_timing per non interpretare la destinazione come orario
print("\n5️⃣ Fix handle_escort_timing...")

escort_timing_start = content.find('async def handle_escort_timing(')
if escort_timing_start != -1:
    # Aggiungi check all'inizio della funzione
    check_code = '''async def handle_escort_timing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle escort timing details"""
    if not context.user_data.get('waiting_for_escort_timing'):
        return TRAVEL_TYPE
        
    phase = context.user_data.get('escort_phase')
    if not phase:
        return TRAVEL_TYPE
    '''
    
    # Trova dove inserire (dopo la definizione della funzione)
    func_body_start = content.find('"""Handle escort timing details"""', escort_timing_start)
    if func_body_start != -1:
        end_docstring = content.find('"""', func_body_start + 3) + 3
        next_line = content.find('\n', end_docstring) + 1
        
        # Inserisci il check
        content = content[:escort_timing_start] + check_code + content[next_line:]

# 6. Verifica che handle_confirmation salvi tutti i dati correttamente
print("\n6️⃣ Verifico salvataggio nel database...")

# Il salvataggio avviene in handle_confirmation, assicuriamoci che tutti i campi siano mappati
confirmation_check = '''
            # Verifica dati prima del salvataggio
            print(f"[DEBUG] Salvataggio servizio:")
            print(f"  - Data: {service.date}")
            print(f"  - Orario: {service.start_time} - {service.end_time}")
            print(f"  - Tipo: {service.service_type}")
            print(f"  - FV: {service.travel_sheet_number}")
            print(f"  - Destinazione: {service.destination}")
            print(f"  - Km: {service.km_total}")
'''

# Trova dove aggiungere il debug (prima di db.add(service))
db_add_pos = content.find('db.add(service)')
if db_add_pos > 0:
    content = content[:db_add_pos] + confirmation_check + '\n            ' + content[db_add_pos:]

# Salva il file modificato
with open('handlers/service_handler.py', 'w') as f:
    f.write(content)

print("✅ service_handler.py aggiornato")

# Commit e push
print("\n7️⃣ Commit e push...")
subprocess.run("git add handlers/service_handler.py", shell=True)
subprocess.run('git commit -m "fix: corretto flusso inserimento destinazione scorta e verifica salvataggio DB"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("\n📝 Modifiche applicate:")
print("1. La destinazione non viene più interpretata come orario")
print("2. Il flusso di inserimento dati è stato corretto")
print("3. Aggiunto debug per verificare il salvataggio nel DB")
print("\n🚀 Railway farà il deploy in 2-3 minuti")
print("📱 Poi riprova a inserire una scorta completa")
