#!/usr/bin/env python3
"""
Test database operations
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import SessionLocal, init_db
from database.models import User
from datetime import datetime

def test_database():
    """Test database operations"""
    print("🔍 Test Database Operations")
    print("=" * 50)
    
    # Initialize database
    print("\n1️⃣ Inizializzazione database...")
    try:
        init_db()
        print("✅ Database inizializzato")
    except Exception as e:
        print(f"❌ Errore init: {e}")
        return
    
    # Test connection
    print("\n2️⃣ Test connessione...")
    db = SessionLocal()
    try:
        # Count users
        user_count = db.query(User).count()
        print(f"✅ Connessione OK - Utenti nel DB: {user_count}")
        
        # List all users
        if user_count > 0:
            print("\n3️⃣ Utenti registrati:")
            users = db.query(User).all()
            for user in users:
                print(f"   - {user.first_name} ({user.telegram_id})")
                print(f"     Grado: {user.rank or 'Non impostato'}")
                print(f"     Comando: {user.command or 'Non impostato'}")
                print(f"     IRPEF: {int(user.irpef_rate * 100)}%")
                print(f"     Turno base: {user.base_shift_hours} ore")
                print()
        
        # Test write operation
        print("\n4️⃣ Test scrittura...")
        test_user = db.query(User).first()
        if test_user:
            old_command = test_user.command
            test_user.command = "TEST COMANDO"
            db.commit()
            
            # Verify
            db.refresh(test_user)
            if test_user.command == "TEST COMANDO":
                print("✅ Scrittura OK")
                # Restore
                test_user.command = old_command
                db.commit()
                print("✅ Ripristinato valore originale")
            else:
                print("❌ Errore scrittura")
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
    
    print("\n" + "=" * 50)
    print("✅ Test completato!")

if __name__ == "__main__":
    test_database()
