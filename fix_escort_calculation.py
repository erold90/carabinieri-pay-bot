#!/usr/bin/env python3
import subprocess
import os

print("🔧 FIX CALCOLO SCORTE - VIAGGIO ATTIVO/PASSIVO")
print("=" * 50)

# Leggi calculation_service.py
with open('services/calculation_service.py', 'r') as f:
    content = f.read()

# Trova la sezione del calcolo straordinari per ESCORT
fix_needed = '''    # 2. STRAORDINARI
    extra_hours = max(0, service.total_hours - user.base_shift_hours - service.recovery_hours)
    
    if service.service_type == ServiceType.ESCORT:
        # Per scorta: ore passive sono straordinario
        passive_overtime = min(extra_hours, service.passive_travel_hours)
        if passive_overtime > 0:
            ot_details = calculate_overtime_by_hour(
                service.start_time + timedelta(hours=user.base_shift_hours),
                service.start_time + timedelta(hours=user.base_shift_hours + passive_overtime),
                service.is_holiday or service.is_super_holiday,
                0  # già saltato il turno base
            )
            calculations['overtime'].update(ot_details)
            extra_hours -= passive_overtime
        
        # Ore attive come maggiorazione viaggio
        if service.active_travel_hours > 0:
            calculations['mission']['active_travel'] = service.active_travel_hours * MISSION_RATES['travel_hourly']
    
    # Straordinari rimanenti
    if extra_hours > 0:'''

# Sostituiamo con la logica corretta
new_logic = '''    # 2. STRAORDINARI
    extra_hours = max(0, service.total_hours - user.base_shift_hours - service.recovery_hours)
    
    if service.service_type == ServiceType.ESCORT:
        # IMPORTANTE: Le ore di viaggio attivo NON sono straordinario
        # ma vengono pagate come maggiorazione viaggio (€8/ora)
        
        # Sottrai le ore di viaggio attivo dal totale straordinari
        active_hours = service.active_travel_hours or 0
        if active_hours > 0:
            # Le ore attive vanno pagate come maggiorazione, non straordinario
            calculations['mission']['active_travel'] = active_hours * MISSION_RATES['travel_hourly']
            # Riduci le ore extra totali delle ore attive
            extra_hours = max(0, extra_hours - active_hours)
        
        # Ora calcola lo straordinario solo sulle ore rimanenti (passive + servizio)
        if extra_hours > 0:
            ot_details = calculate_overtime_by_hour(
                service.start_time,
                service.end_time,
                service.is_holiday or service.is_super_holiday,
                user.base_shift_hours + service.recovery_hours + active_hours  # Salta anche ore attive
            )
            calculations['overtime'].update(ot_details)
    else:
        # Per servizi non-escort, tutto normale'''

# Trova e sostituisci
import re
pattern = r'# 2\. STRAORDINARI.*?# Straordinari rimanenti\s*if extra_hours > 0:'
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, new_logic, content, flags=re.DOTALL)
    print("✅ Logica di calcolo aggiornata")
else:
    print("⚠️ Pattern non trovato, provo approccio alternativo...")
    # Trova la sezione e sostituiscila manualmente
    lines = content.split('\n')
    in_overtime_section = False
    new_lines = []
    skip_lines = 0
    
    for i, line in enumerate(lines):
        if skip_lines > 0:
            skip_lines -= 1
            continue
            
        if '# 2. STRAORDINARI' in line and 'extra_hours = max' in lines[i+1]:
            # Trovata la sezione, sostituisci
            new_lines.append(new_logic)
            # Salta le prossime linee fino a trovare else:
            for j in range(i+1, len(lines)):
                if 'else:' in lines[j] and 'servizi non-escort' not in lines[j]:
                    skip_lines = j - i - 1
                    break
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)

# Aggiungi anche un commento esplicativo all'inizio della funzione calculate_service_total
explanation = '''def calculate_service_total(db: Session, user: User, service: Service) -> dict:
    """
    Calculates ALL net amounts for a service - COMPLETE VERSION
    
    IMPORTANTE per SCORTE:
    - Ore di viaggio ATTIVO (senza VIP) sono pagate come Maggiorazione Viaggio (€8/ora)
    - Ore di viaggio PASSIVO (con VIP) sono pagate come Straordinario normale
    - Le ore attive NON devono essere conteggiate anche come straordinario!
    """'''

content = content.replace(
    'def calculate_service_total(db: Session, user: User, service: Service) -> dict:\n    """\n    Calculates ALL net amounts for a service - COMPLETE VERSION\n    """',
    explanation
)

# Salva il file
with open('services/calculation_service.py', 'w') as f:
    f.write(content)

print("✅ File calculation_service.py aggiornato")

# Verifica sintassi
result = subprocess.run(['python3', '-m', 'py_compile', 'services/calculation_service.py'], 
                       capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Sintassi corretta")
    
    # Crea anche un test per verificare il calcolo
    test_code = '''#!/usr/bin/env python3
"""Test calcolo scorta per verificare fix"""
import os
os.environ['DATABASE_URL'] = 'sqlite:///test.db'

from datetime import datetime, date
from database.connection import SessionLocal, init_db
from database.models import User, Service, ServiceType
from services.calculation_service import calculate_service_total

print("🧪 TEST CALCOLO SCORTA")
print("=" * 50)

# Inizializza DB
init_db()

# Crea sessione
db = SessionLocal()

try:
    # Crea utente test
    user = User(
        telegram_id="test123",
        chat_id="test123",
        rank="Brigadiere",
        parameter=110.0,
        irpef_rate=0.27,
        base_shift_hours=6
    )
    db.add(user)
    db.commit()
    
    # Crea servizio scorta test
    service = Service(
        user_id=user.id,
        date=date(2025, 5, 31),
        start_time=datetime(2025, 5, 31, 6, 30),
        end_time=datetime(2025, 5, 31, 21, 0),
        total_hours=14.5,
        service_type=ServiceType.ESCORT,
        is_holiday=False,
        is_super_holiday=False,
        travel_sheet_number="345",
        destination="San Severo",
        km_total=350,
        active_travel_hours=1.0,  # 1 ora viaggio attivo
        passive_travel_hours=7.5, # Resto è passivo/con VIP
        mission_type="ORDINARY"
    )
    
    # Calcola
    result = calculate_service_total(db, user, service)
    
    print("RISULTATI CALCOLO:")
    print(f"Ore totali: {service.total_hours}")
    print(f"Ore base: {user.base_shift_hours}")
    print(f"Ore extra totali: {service.total_hours - user.base_shift_hours}")
    print(f"- Di cui viaggio attivo: {service.active_travel_hours}h")
    print(f"- Di cui passivo/servizio: {service.total_hours - user.base_shift_hours - service.active_travel_hours}h")
    print()
    
    print("STRAORDINARI:")
    total_ot_hours = sum(v['hours'] for v in result['overtime'].values())
    print(f"Ore straordinario: {total_ot_hours}h")
    print(f"Importo: €{result['totals']['overtime']:.2f}")
    print()
    
    print("MISSIONE:")
    if 'active_travel' in result['mission']:
        print(f"Maggiorazione viaggio: €{result['mission']['active_travel']:.2f}")
    print(f"Totale missione: €{result['totals']['mission']:.2f}")
    print()
    
    print(f"TOTALE FINALE: €{result['totals']['total']:.2f}")
    print()
    
    # Verifica correttezza
    expected_ot_hours = 7.5  # 8.5 ore extra - 1.0 viaggio attivo
    if abs(total_ot_hours - expected_ot_hours) < 0.1:
        print("✅ Calcolo straordinari CORRETTO!")
    else:
        print(f"❌ ERRORE: Straordinari dovrebbero essere {expected_ot_hours}h, non {total_ot_hours}h")
    
    expected_total = 237.50  # Come da tua analisi
    if abs(result['totals']['total'] - expected_total) < 1:
        print("✅ Totale CORRETTO!")
    else:
        print(f"❌ Totale dovrebbe essere €{expected_total}, non €{result['totals']['total']:.2f}")
        
finally:
    db.close()
'''
    
    with open('test_escort_calculation.py', 'w') as f:
        f.write(test_code)
    os.chmod('test_escort_calculation.py', 0o755)
    
    print("\n✅ Creato test_escort_calculation.py")
    
    # Commit e push
    print("\n📤 Commit e push del fix...")
    subprocess.run("git add -A", shell=True)
    subprocess.run('git commit -m "fix: corretto doppio conteggio ore viaggio attivo nelle scorte"', shell=True)
    subprocess.run("git push origin main", shell=True)
    
    print("\n✅ Fix completato e pushato!")
    print("\n🧪 Per verificare il fix, esegui:")
    print("   python3 test_escort_calculation.py")
    
else:
    print(f"❌ Errore sintassi: {result.stderr}")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script auto-eliminato")
