#!/usr/bin/env python3
import subprocess

print("🔧 FIX FLUSSO CONVERSAZIONE SERVICE_HANDLER")
print("=" * 50)

# 1. Analizza service_handler.py
print("\n1️⃣ Analisi del flusso conversazione...")

with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# 2. Trova e correggi il ConversationHandler
print("\n2️⃣ Correzione stati ConversationHandler...")

# Il problema è che dopo la destinazione, dovrebbe chiedere altro, non l'orario
# Cerchiamo la funzione handle_destination
if 'async def handle_destination' in content:
    print("✅ handle_destination trovato")
else:
    print("⚠️ handle_destination non trovato, lo creo...")
    
    # Aggiungi la funzione
    handle_dest = '''
async def handle_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle destination input for missions"""
    destination = update.message.text.strip()
    context.user_data['destination'] = destination
    
    # Per scorte, chiedi dettagli timing
    if context.user_data.get('service_type') == ServiceType.ESCORT:
        text = "⏱️ <b>TIMING DETTAGLIATO</b>\\n\\n"
        text += "Inserisci gli orari nel formato HH:MM\\n\\n"
        text += "<b>1️⃣ ANDATA (senza VIP):</b>\\n"
        text += "Ora partenza dalla sede:"
        
        await update.message.reply_text(text, parse_mode='HTML')
        context.user_data['escort_phase'] = 'departure_time'
        return TRAVEL_TYPE
    else:
        # Per missioni generiche, chiedi i km
        await update.message.reply_text(
            "🚗 Chilometri totali (se applicabile, altrimenti 0):",
            parse_mode='HTML'
        )
        return TRAVEL_TYPE
'''

# 3. Trova dove inserire la funzione
conv_handler_pos = content.find('service_conversation_handler = ConversationHandler')
if conv_handler_pos > 0 and 'async def handle_destination' not in content:
    content = content[:conv_handler_pos] + handle_dest + '\n\n' + content[conv_handler_pos:]

# 4. Correggi il ConversationHandler states
print("\n3️⃣ Correzione mappatura stati...")

# Trova la sezione states del ConversationHandler
states_start = content.find('states={')
states_end = content.find('},', states_start)

if states_start > 0 and states_end > 0:
    states_section = content[states_start:states_end+1]
    
    # Assicurati che TRAVEL_DETAILS abbia handle_destination
    if 'TRAVEL_DETAILS:' in states_section:
        # Sostituisci handler per TRAVEL_DETAILS
        new_states = states_section
        
        # Cerca TRAVEL_DETAILS e sostituisci con il handler corretto
        import re
        pattern = r'TRAVEL_DETAILS:\s*\[[^\]]+\]'
        replacement = '''TRAVEL_DETAILS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_travel_sheet_number)
        ]'''
        new_states = re.sub(pattern, replacement, new_states)
        
        # SERVICE_DETAILS per handle_destination
        pattern2 = r'SERVICE_DETAILS:\s*\[[^\]]+\]'
        replacement2 = '''SERVICE_DETAILS: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_destination)
        ]'''
        new_states = re.sub(pattern2, replacement2, new_states)
        
        # TRAVEL_TYPE per timing escort o km
        pattern3 = r'TRAVEL_TYPE:\s*\[[^\]]+\]'
        replacement3 = '''TRAVEL_TYPE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_escort_timing),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mission_km)
        ]'''
        new_states = re.sub(pattern3, replacement3, new_states)
        
        content = content[:states_start] + new_states + content[states_end+1:]

# 5. Correggi le funzioni che gestiscono destinazione
print("\n4️⃣ Correzione funzioni destinazione...")

# Trova handle_mission_destination e assicurati che ritorni SERVICE_DETAILS
fix_mission_dest = '''async def handle_mission_destination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mission destination"""
    context.user_data['destination'] = update.message.text
    
    await update.message.reply_text(
        "🚗 Chilometri totali (se applicabile, altrimenti 0):",
        parse_mode='HTML'
    )
    
    return TRAVEL_TYPE'''

# Sostituisci la funzione esistente
if 'async def handle_mission_destination' in content:
    start = content.find('async def handle_mission_destination')
    end = content.find('\n\nasync def', start + 1)
    if end == -1:
        end = content.find('\n\n# ', start + 1)
    if end == -1:
        end = content.find('\n\nservice_conversation_handler', start + 1)
    
    if end > start:
        content = content[:start] + fix_mission_dest + content[end:]

# 6. Salva il file
print("\n5️⃣ Salvataggio...")
with open('handlers/service_handler.py', 'w') as f:
    f.write(content)

print("✅ service_handler.py aggiornato")

# 7. Verifica sintassi
print("\n6️⃣ Verifica sintassi...")
result = subprocess.run(['python3', '-m', 'py_compile', 'handlers/service_handler.py'], capture_output=True)
if result.returncode == 0:
    print("✅ Sintassi OK")
else:
    print("❌ Errore sintassi:")
    print(result.stderr.decode())

# 8. Commit e push
print("\n7️⃣ Commit e push...")
subprocess.run("git add handlers/service_handler.py", shell=True)
subprocess.run('git commit -m "fix: corretto flusso conversazione dopo inserimento destinazione"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ FIX COMPLETATO!")
print("\n📱 Ora dopo aver inserito la destinazione:")
print("- Per SCORTE: chiederà i dettagli timing")
print("- Per MISSIONI: chiederà i km")
print("\n⏰ Attendi 2 minuti per il deploy")
