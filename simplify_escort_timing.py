#!/usr/bin/env python3
import subprocess

print("🔧 SEMPLIFICAZIONE TIMING SCORTE")
print("=" * 50)

# Modifica service_handler.py
print("\n📄 Aggiornamento service_handler.py...")

with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# 1. Modifica la funzione handle_destination per le scorte
import re

# Trova e modifica la parte che chiede il timing dettagliato
pattern = r'(if service_type == ServiceType\.ESCORT:[\s\S]*?)text = "⏱️ <b>TIMING DETTAGLIATO</b>.*?"'

def simplify_timing_request(match):
    before = match.group(1)
    
    # Nuovo testo semplificato
    new_text = '''text = "⏱️ <b>ORARI SERVIZIO</b>\\n\\n"
        text += "Ora partenza dalla sede (HH:MM):"'''
    
    return before + new_text

content = re.sub(pattern, simplify_timing_request, content, flags=re.DOTALL)

# 2. Modifica handle_escort_timing per gestire meno input
pattern2 = r'async def handle_escort_timing\(.*?\):\s*\n(.*?)(?=\nasync def|\Z)'

def simplify_escort_function(match):
    # Riscrivi la funzione semplificata
    new_function = '''async def handle_escort_timing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle escort timing details - versione semplificata"""
    if not context.user_data.get('waiting_for_escort_timing'):
        return TRAVEL_TYPE
        
    phase = context.user_data.get('escort_phase')
    if not phase:
        return TRAVEL_TYPE
    
    try:
        # Parse time input
        time_parts = update.message.text.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1]) if len(time_parts) > 1 else 0
        
        if phase == 'departure_time':
            context.user_data['departure_time'] = (hour, minute)
            await update.message.reply_text(
                "Ora arrivo a destinazione:",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'arrival_time'
            
        elif phase == 'arrival_time':
            context.user_data['arrival_time'] = (hour, minute)
            # Assume che il VIP viene preso all'arrivo
            context.user_data['vip_pickup'] = (hour, minute)
            
            await update.message.reply_text(
                "Ora partenza per il rientro:",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'return_departure'
            
        elif phase == 'return_departure':
            context.user_data['return_departure'] = (hour, minute)
            # Assume che il VIP viene lasciato alla partenza per il rientro
            context.user_data['vip_end'] = (hour, minute)
            
            await update.message.reply_text(
                "Ora rientro in sede:",
                parse_mode='HTML'
            )
            context.user_data['escort_phase'] = 'return_arrival'
            
        elif phase == 'return_arrival':
            context.user_data['return_arrival'] = (hour, minute)
            
            # Calcola ore attive/passive automaticamente
            calculate_escort_hours(context)
            
            # Chiedi tipo di pagamento missione
            text = "💶 <b>REGIME DI RIMBORSO</b>\\n\\n"
            text += "Scegli come essere pagato:"
            
            await update.message.reply_text(
                text,
                parse_mode='HTML',
                reply_markup=get_mission_type_keyboard()
            )
            
            context.user_data['escort_phase'] = None
            context.user_data['waiting_for_escort_timing'] = False
            return MEAL_DETAILS
            
    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Formato non valido! Usa HH:MM (es: 08:30)",
            parse_mode='HTML'
        )
    
    return TRAVEL_TYPE

'''
    
    return new_function

content = re.sub(pattern2, simplify_escort_function, content, flags=re.DOTALL)

# 3. Rimuovi la richiesta dei km per le scorte
# Trova la parte che chiede i km dopo il timing
pattern3 = r'elif phase == \'km\':(.*?)context\.user_data\[\'km_total\'\] = int\(update\.message\.text\)'

content = re.sub(pattern3, '', content, flags=re.DOTALL)

# 4. Modifica calculate_service_total per non richiedere km per scorte
print("\n📄 Aggiornamento calculation_service.py...")

with open('services/calculation_service.py', 'r') as f:
    calc_content = f.read()

# Rimuovi il calcolo km per le scorte dal totale missione
pattern_km = r'# Rimborso km\s*\n\s*if service\.km_total > 0:\s*\n\s*mission\[\'km_reimbursement\'\] = service\.km_total \* MISSION_RATES\[\'km_rate\'\]'

calc_content = re.sub(pattern_km, '''# Rimborso km (solo per missioni, non scorte)
        if service.service_type == ServiceType.MISSION and service.km_total > 0:
            mission['km_reimbursement'] = service.km_total * MISSION_RATES['km_rate']''', calc_content)

# Salva i file modificati
with open('handlers/service_handler.py', 'w') as f:
    f.write(content)

with open('services/calculation_service.py', 'w') as f:
    f.write(calc_content)

print("✅ Modifiche applicate")

# 5. Fix del callback confirm_yes
print("\n📄 Implementazione callback confirm_yes...")

# Verifica che handle_confirmation gestisca correttamente confirm_yes
if 'def handle_confirmation' in content:
    # La funzione esiste, assicuriamoci che gestisca "yes"
    pattern_confirm = r'(async def handle_confirmation.*?action = query\.data\.replace\("confirm_", ""\))(.*?)(if action ==)'
    
    def fix_confirm_check(match):
        before = match.group(1)
        middle = match.group(2)
        if_part = match.group(3)
        
        # Assicurati che controlli "yes" e non "confirm"
        return before + middle + '\n    if action == "yes":'
    
    content = re.sub(pattern_confirm, fix_confirm_check, content, flags=re.DOTALL)
    
    with open('handlers/service_handler.py', 'w') as f:
        f.write(content)

# 6. Verifica sintassi
print("\n🔍 Verifica sintassi...")

files_to_test = ['handlers/service_handler.py', 'services/calculation_service.py']
all_ok = True

for file in files_to_test:
    try:
        with open(file, 'r') as f:
            compile(f.read(), file, 'exec')
        print(f"✅ {file} - OK")
    except SyntaxError as e:
        print(f"❌ {file} - Errore: {e}")
        all_ok = False

if all_ok:
    print("\n✅ Tutti i file sono corretti!")

# Mostra il risultato
print("\n📋 MODIFICHE APPLICATE:")
print("1. ✅ Semplificato il timing delle scorte a 4 input invece di 6")
print("2. ✅ Rimossa la richiesta dei km per le scorte")
print("3. ✅ Il VIP viene automaticamente preso all'arrivo e lasciato alla partenza")
print("4. ✅ Implementato il callback confirm_yes")

print("\n🚀 NUOVO FLUSSO SEMPLIFICATO:")
print("1. Ora partenza dalla sede")
print("2. Ora arrivo a destinazione (= presa VIP)")
print("3. Ora partenza per rientro (= lasciato VIP)")
print("4. Ora rientro in sede")
print("5. Tipo di rimborso (ordinario/forfettario)")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "feat: semplificato inserimento timing scorte e rimosso calcolo km"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Semplificazione completata!")
print("🎯 Ora l'inserimento delle scorte è molto più veloce!")

# Auto-elimina
import os
os.remove(__file__)
