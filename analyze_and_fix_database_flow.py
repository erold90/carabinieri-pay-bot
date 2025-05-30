#!/usr/bin/env python3
import subprocess
import os

print("🔍 Analisi completa flusso database CarabinieriPayBot")
print("=" * 50)

# 1. Verifica che l'utente sia creato correttamente al primo accesso
print("\n1️⃣ Verifico creazione utente in start_handler.py...")

with open('handlers/start_handler.py', 'r') as f:
    start_content = f.read()

# Verifica che i campi obbligatori siano impostati
if 'db_user = User(' in start_content:
    print("✅ Creazione utente presente")
    
    # Verifica i default values
    required_defaults = [
        'irpef_rate',  # default 0.27
        'base_shift_hours',  # default 6
        'current_year_leave',  # default 32
        'parameter'  # default 108.5
    ]
    
    print("\n   Campi con valori default:")
    for field in required_defaults:
        if field in start_content:
            print(f"   ✅ {field}")
        else:
            print(f"   ❌ {field} - MANCANTE!")

# 2. Verifica il flusso di salvataggio Service
print("\n\n2️⃣ Verifico salvataggio Service in service_handler.py...")

with open('handlers/service_handler.py', 'r') as f:
    service_content = f.read()

# Crea uno script per fixare il salvataggio completo
fix_service_save = '''#!/usr/bin/env python3
import subprocess

print("🔧 Fix salvataggio completo Service nel database")
print("=" * 50)

with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# Trova handle_confirmation e assicurati che salvi tutto
confirmation_start = content.find('async def handle_confirmation(')
if confirmation_start != -1:
    # Trova la sezione dove crea il Service
    service_creation = content.find('db.add(service)', confirmation_start)
    
    if service_creation > 0:
        # Aggiungi il salvataggio completo con tutti i calcoli
        new_save_section = """
            # Calcola tutti gli importi PRIMA di salvare
            calculations = context.user_data.get('calculations', {})
            
            # Imposta gli importi calcolati
            service.overtime_amount = calculations.get('totals', {}).get('overtime', 0)
            service.allowances_amount = calculations.get('totals', {}).get('allowances', 0)
            service.mission_amount = calculations.get('totals', {}).get('mission', 0)
            service.total_amount = calculations.get('totals', {}).get('total', 0)
            service.calculation_details = calculations
            
            # Per scorte, calcola il rimborso km
            if service.service_type == ServiceType.ESCORT and service.km_total > 0:
                km_reimbursement = service.km_total * 0.35  # €0.35/km
                service.mission_amount += km_reimbursement
                service.total_amount += km_reimbursement
            
            # Salva il servizio
            db.add(service)
            db.flush()  # Ottieni l'ID prima del commit
            
            # Crea record Overtime per ore extra
            if service.total_hours > user.base_shift_hours:
                extra_hours = service.total_hours - user.base_shift_hours
                
                # Determina il tipo di straordinario
                from database.models import Overtime, OvertimeType
                from services.calculation_service import get_overtime_type
                
                ot_type = get_overtime_type(
                    service.start_time,
                    service.is_holiday or service.is_super_holiday
                )
                
                # Calcola tariffa
                rate = OVERTIME_RATES[ot_type.value.lower()]
                amount = extra_hours * rate
                
                overtime = Overtime(
                    user_id=user.id,
                    service_id=service.id,
                    date=service.date,
                    hours=extra_hours,
                    overtime_type=ot_type,
                    hourly_rate=rate,
                    amount=amount,
                    is_paid=False  # Di default non pagato
                )
                db.add(overtime)
            
            # Crea TravelSheet se è una scorta
            if service.service_type == ServiceType.ESCORT and service.travel_sheet_number:
                from database.models import TravelSheet
                
                travel_sheet = TravelSheet(
                    user_id=user.id,
                    service_id=service.id,
                    sheet_number=service.travel_sheet_number,
                    date=service.date,
                    destination=service.destination,
                    amount=service.mission_amount + (service.km_total * 0.35)
                )
                db.add(travel_sheet)
            
            # Aggiorna licenze se richiamato
            if service.called_from_leave:
                user.current_year_leave_used += 1
                
            # Commit finale
            db.commit()
            
            print(f"[DB] Servizio salvato - ID: {service.id}")
            print(f"[DB] Totale: €{service.total_amount:.2f}")
            print(f"[DB] Straordinari: €{service.overtime_amount:.2f}")
            print(f"[DB] Indennità: €{service.allowances_amount:.2f}")
            print(f"[DB] Missione: €{service.mission_amount:.2f}")
"""
        
        # Trova dove inserire (prima di db.add(service))
        insert_pos = content.rfind('db.add(service)', 0, service_creation)
        if insert_pos > 0:
            # Rimuovi il vecchio db.add e sostituisci con il nuovo
            end_commit = content.find('db.commit()', insert_pos)
            if end_commit > 0:
                end_line = content.find('\\n', end_commit)
                content = content[:insert_pos] + new_save_section + content[end_line:]

# Salva il file aggiornato
with open('handlers/service_handler.py', 'w') as f:
    f.write(content)

print("✅ Aggiornato salvataggio completo nel database")

# Aggiungi anche gli import necessari all'inizio del file
with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# Aggiungi import se mancanti
if 'from config.constants import OVERTIME_RATES' not in content:
    import_pos = content.find('from config.constants import')
    if import_pos > 0:
        line_end = content.find('\\n', import_pos)
        old_import = content[import_pos:line_end]
        new_import = old_import.rstrip(')') + ', OVERTIME_RATES)'
        content = content.replace(old_import, new_import)
        
        with open('handlers/service_handler.py', 'w') as f:
            f.write(content)
        print("✅ Aggiunto import OVERTIME_RATES")

# Commit
subprocess.run("git add handlers/service_handler.py", shell=True)
subprocess.run('git commit -m "fix: salvataggio completo Service con Overtime e TravelSheet automatici"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\\n✅ Fix completato!")
'''

# Salva lo script di fix
with open('fix_complete_db_save.py', 'w') as f:
    f.write(fix_service_save)

os.chmod('fix_complete_db_save.py', 0o755)

print("\n✅ Creato script fix_complete_db_save.py")

# 3. Verifica i campi necessari per ogni tipo di servizio
print("\n\n3️⃣ Campi necessari per tipo di servizio:")

print("\n📍 SERVIZIO LOCALE:")
print("   - date, start_time, end_time, total_hours")
print("   - is_holiday, is_super_holiday")
print("   - called_from_leave/rest")
print("   - Calcoli automatici: overtime, allowances")

print("\n🚔 SERVIZIO SCORTA:")
print("   - Tutti i campi del locale +")
print("   - travel_sheet_number (obbligatorio)")
print("   - destination (obbligatorio)")
print("   - km_total")
print("   - active_travel_hours, passive_travel_hours")
print("   - Crea automaticamente: TravelSheet")

print("\n✈️ MISSIONE:")
print("   - Tutti i campi del locale +")
print("   - destination")
print("   - mission_type (ORDINARY/FORFEIT)")
print("   - meals_consumed")
print("   - km_total (opzionale)")

# 4. Verifica che tutti i calcoli vengano eseguiti
print("\n\n4️⃣ Verifico calculation_service.py...")

if os.path.exists('services/calculation_service.py'):
    with open('services/calculation_service.py', 'r') as f:
        calc_content = f.read()
    
    required_functions = [
        'calculate_service_total',
        'is_holiday',
        'is_super_holiday',
        'get_overtime_type'
    ]
    
    print("\n   Funzioni di calcolo:")
    for func in required_functions:
        if f'def {func}' in calc_content:
            print(f"   ✅ {func}")
        else:
            print(f"   ❌ {func} - MANCANTE!")

print("\n\n" + "=" * 50)
print("📋 RIEPILOGO:")
print("\n1. L'utente deve avere tutti i campi configurati (grado, IRPEF, ecc)")
print("2. Ogni Service deve salvare tutti i calcoli")
print("3. Overtime e TravelSheet devono essere creati automaticamente")
print("4. I calcoli devono essere eseguiti PRIMA del salvataggio")
print("\n🔧 Esegui lo script di fix:")
print("python3 fix_complete_db_save.py")
