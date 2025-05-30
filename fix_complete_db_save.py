#!/usr/bin/env python3
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
                end_line = content.find('\n', end_commit)
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
        line_end = content.find('\n', import_pos)
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

print("\n✅ Fix completato!")
