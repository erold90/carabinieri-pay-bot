#!/usr/bin/env python3
"""Test connessione database"""
import os
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///test.db')

from database.connection import SessionLocal, init_db
from database.models import User

print("🧪 TEST DATABASE")
print("=" * 50)

try:
    init_db()
    print("✅ Database inizializzato")
    
    db = SessionLocal()
    user_count = db.query(User).count()
    print(f"👥 Utenti nel database: {user_count}")
    
    # Test creazione utente
    test_user = User(
        telegram_id="test123",
        chat_id="test123",
        username="test",
        first_name="Test",
        last_name="User"
    )
    db.add(test_user)
    db.commit()
    print("✅ Test creazione utente OK")
    
    # Rimuovi test user
    db.query(User).filter(User.telegram_id == "test123").delete()
    db.commit()
    db.close()
    
    print("✅ Database funzionante!")
    
except Exception as e:
    print(f"❌ Errore database: {e}")
    import traceback
    traceback.print_exc()
