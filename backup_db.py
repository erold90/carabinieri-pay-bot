#!/usr/bin/env python3
"""Backup automatico database"""
import os
import subprocess
from datetime import datetime

def backup_database():
    """Crea backup del database"""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("❌ DATABASE_URL non trovato")
        return
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{timestamp}.sql"
    
    try:
        if db_url.startswith('postgresql'):
            # Backup PostgreSQL
            subprocess.run([
                'pg_dump',
                db_url,
                '-f', backup_file
            ], check=True)
            print(f"✅ Backup creato: {backup_file}")
        else:
            print("⚠️  Backup disponibile solo per PostgreSQL")
    except Exception as e:
        print(f"❌ Errore backup: {e}")

if __name__ == "__main__":
    backup_database()
