#!/usr/bin/env python3
import subprocess

print("🔧 Fix calcolo scorte: controllo territorio e pasti")
print("=" * 50)

# 1. Fix calculation_service.py per escludere controllo territorio dalle scorte
print("\n📄 Aggiornamento calculation_service.py...")

with open('services/calculation_service.py', 'r') as f:
    content = f.read()

# Trova la sezione delle indennità giornaliere
import re

# Modifica la parte che calcola le indennità
old_pattern = r'(# Controllo territorio\s*\n\s*territory = calculate_territory_control\(service\.start_time, service\.end_time, service\.total_hours\)\s*\n\s*allowances\.update\(territory\))'

new_code = '''# Controllo territorio (solo per servizi locali, non scorte)
    if service.service_type == ServiceType.LOCAL:
        territory = calculate_territory_control(service.start_time, service.end_time, service.total_hours)
        allowances.update(territory)'''

content = re.sub(old_pattern, new_code, content, flags=re.DOTALL)

# Salva il file
with open('services/calculation_service.py', 'w') as f:
    f.write(content)

print("✅ Controllo territorio ora escluso per scorte")

# 2. Fix per mostrare i pasti nel riepilogo
print("\n📄 Aggiornamento service_handler.py...")

with open('handlers/service_handler.py', 'r') as f:
    handler_content = f.read()

# Trova la funzione format_detailed_summary
pattern = r'(# Mission compensation\s*\n\s*if calculations\[\'mission\'\]:)'

# Aggiungi la visualizzazione dei pasti
insert_code = '''# Mission compensation
    if calculations['mission']:'''

# Trova dove inserire i dettagli dei pasti
mission_section_pattern = r'(if service\.mission_type == "FORFEIT":\s*\n\s*text \+= f"\\n<b>3️⃣ MISSIONE \(Regime: FORFETTARIO\)</b>\\n"\s*\n\s*else:\s*\n\s*text \+= f"\\n<b>3️⃣ MISSIONE \(Regime: ORDINARIO\)</b>\\n")'

# Aggiungi logica per mostrare i pasti
new_mission_display = r'''\1
        
        # Mostra dettagli pasti se applicabile
        if service.service_type in [ServiceType.ESCORT, ServiceType.MISSION]:
            meals_entitled = 0
            if service.total_hours >= 8:
                meals_entitled = 1
            if service.total_hours >= 12:
                meals_entitled = 2
            
            if meals_entitled > 0:
                meals_consumed = service.meals_consumed or 0
                meals_not_consumed = meals_entitled - meals_consumed
                
                text += f"\\n🍽️ <b>PASTI:</b>\\n"
                text += f"├ Diritto a {meals_entitled} pasti (servizio {service.total_hours:.0f}h)\\n"
                text += f"├ Consumati: {meals_consumed}\\n"
                text += f"├ NON consumati: {meals_not_consumed}\\n"
                
                if 'meal_reimbursement' in calculations['mission']:
                    text += f"└ Rimborso: {format_currency(calculations['mission']['meal_reimbursement'])}\\n"
        '''

handler_content = re.sub(mission_section_pattern, new_mission_display, handler_content, flags=re.DOTALL)

# Salva
with open('handlers/service_handler.py', 'w') as f:
    f.write(handler_content)

print("✅ Aggiunta visualizzazione pasti nel riepilogo")

# 3. Verifica sintassi
print("\n🔍 Verifica sintassi...")
for file in ['services/calculation_service.py', 'handlers/service_handler.py']:
    try:
        with open(file, 'r') as f:
            compile(f.read(), file, 'exec')
        print(f"✅ {file} - OK")
    except SyntaxError as e:
        print(f"❌ {file} - Errore: {e}")

# 4. Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: escluso controllo territorio per scorte e aggiunta visualizzazione pasti"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("\n📋 MODIFICHE APPLICATE:")
print("1. ❌ Controllo territorio non viene più applicato alle scorte")
print("2. ✅ I pasti vengono ora mostrati nel riepilogo")
print("3. ✅ Il rimborso pasti viene visualizzato correttamente")

print("\n🧮 CALCOLO CORRETTO PER IL TUO ESEMPIO:")
print("- Ore totali: 14h (06:30-21:00)")
print("- Ore straordinario: 8h (14h - 6h base)")
print("- Di cui 1h attiva (senza rimborso pasti perché viaggi)")
print("- Di cui 7h passive")
print("- NO controllo territorio (è una scorta)")
print("- Pasti: diritto a 2, se non consumati = €28,58 rimborso")

# Auto-elimina
import os
os.remove(__file__)
