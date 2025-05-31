#!/usr/bin/env python3
"""Test salvataggio servizio diretto"""
import os
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL')

from datetime import datetime, date
from database.connection import SessionLocal, init_db
from database.models import User, Service, ServiceType, Overtime
from services.calculation_service import calculate_service_total

print("🧪 TEST SALVATAGGIO SERVIZIO")
print("=" * 50)

db = SessionLocal()
try:
    # Trova utente esistente
    user = db.query(User).first()
    if not user:
        print("❌ Nessun utente trovato!")
        exit(1)
    
    print(f"👤 Utente: {user.rank} {user.first_name}")
    
    # Crea servizio test
    service = Service(
        user_id=user.id,
        date=date.today(),
        start_time=datetime.now().replace(hour=8, minute=0),
        end_time=datetime.now().replace(hour=14, minute=0),
        total_hours=6.0,
        service_type=ServiceType.LOCAL,
        is_holiday=False,
        is_super_holiday=False
    )
    
    # Calcola totali
    calc = calculate_service_total(db, user, service)
    
    print(f"📊 Calcolo: {calc['totals']['total']:.2f}€")
    
    # Salva
    db.add(service)
    db.commit()
    
    print("✅ Servizio salvato con ID:", service.id)
    
    # Verifica
    saved = db.query(Service).filter(Service.id == service.id).first()
    if saved:
        print("✅ Verifica: servizio presente nel DB")
        print(f"   - Data: {saved.date}")
        print(f"   - Ore: {saved.total_hours}")
        print(f"   - Totale: {saved.total_amount}€")
        
        # Verifica straordinari
        ot_count = db.query(Overtime).filter(Overtime.service_id == saved.id).count()
        print(f"   - Straordinari creati: {ot_count}")
    else:
        print("❌ Servizio non trovato!")
        
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
