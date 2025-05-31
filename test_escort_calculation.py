#!/usr/bin/env python3
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
