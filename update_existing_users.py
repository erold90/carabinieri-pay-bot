#!/usr/bin/env python3
"""
Script per aggiornare utenti esistenti con valori default mancanti
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal, init_db
from database.models import User

def update_existing_users():
    print("🔄 Aggiornamento utenti esistenti...")
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        updated = 0
        
        for user in users:
            changes = []
            
            # Verifica e aggiorna campi mancanti
            if user.irpef_rate is None or user.irpef_rate == 0:
                user.irpef_rate = 0.27
                changes.append("IRPEF: 27%")
            
            if user.base_shift_hours is None or user.base_shift_hours == 0:
                user.base_shift_hours = 6
                changes.append("Turno base: 6h")
            
            if user.parameter is None or user.parameter == 0:
                user.parameter = 108.5
                changes.append("Parametro: 108.5")
            
            if user.current_year_leave is None:
                user.current_year_leave = 32
                changes.append("Licenza annuale: 32gg")
            
            if user.current_year_leave_used is None:
                user.current_year_leave_used = 0
                changes.append("Licenza usata: 0gg")
            
            if user.previous_year_leave is None:
                user.previous_year_leave = 0
                changes.append("Licenza anno prec: 0gg")
            
            if changes:
                print(f"\n📝 Aggiornato {user.first_name or 'Utente'} ({user.telegram_id}):")
                for change in changes:
                    print(f"   - {change}")
                updated += 1
        
        if updated > 0:
            db.commit()
            print(f"\n✅ Aggiornati {updated} utenti")
        else:
            print("\n✅ Tutti gli utenti hanno già i valori corretti")
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    update_existing_users()
