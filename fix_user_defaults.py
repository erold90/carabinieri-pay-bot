#!/usr/bin/env python3
import subprocess
import os

print("🔧 Fix valori default utente in database")
print("=" * 50)

# 1. Fix modello User per avere tutti i default
print("\n1️⃣ Sistemo i default nel modello User...")

with open('database/models.py', 'r') as f:
    models_content = f.read()

# Trova la classe User e verifica i campi
user_class_start = models_content.find('class User(Base):')
if user_class_start != -1:
    # Trova i campi che necessitano default
    
    # Fix irpef_rate default
    old_irpef = 'irpef_rate = Column(Float)'
    new_irpef = 'irpef_rate = Column(Float, default=0.27)'
    if old_irpef in models_content:
        models_content = models_content.replace(old_irpef, new_irpef)
        print("✅ Aggiunto default irpef_rate = 0.27 (27%)")
    
    # Fix base_shift_hours default
    old_shift = 'base_shift_hours = Column(Integer)'
    new_shift = 'base_shift_hours = Column(Integer, default=6)'
    if old_shift in models_content:
        models_content = models_content.replace(old_shift, new_shift)
        print("✅ Aggiunto default base_shift_hours = 6")
    
    # Fix parameter default (già presente ma verifichiamo)
    if 'parameter = Column(Float)' in models_content:
        models_content = models_content.replace(
            'parameter = Column(Float)',
            'parameter = Column(Float, default=108.5)'
        )
        print("✅ Aggiunto default parameter = 108.5")

# Salva models.py aggiornato
with open('database/models.py', 'w') as f:
    f.write(models_content)

print("\n✅ Aggiornati default nel modello User")

# 2. Fix creazione utente in start_handler
print("\n2️⃣ Sistemo creazione utente in start_handler...")

with open('handlers/start_handler.py', 'r') as f:
    start_content = f.read()

# Trova la creazione dell'utente
user_creation_pos = start_content.find('db_user = User(')
if user_creation_pos != -1:
    # Trova la fine della creazione (cerca la parentesi di chiusura)
    paren_count = 1
    i = start_content.find('(', user_creation_pos) + 1
    end_pos = i
    while i < len(start_content) and paren_count > 0:
        if start_content[i] == '(':
            paren_count += 1
        elif start_content[i] == ')':
            paren_count -= 1
            if paren_count == 0:
                end_pos = i
        i += 1
    
    # Estrai la creazione attuale
    current_creation = start_content[user_creation_pos:end_pos+1]
    
    # Aggiungi i campi mancanti se non presenti
    new_fields = []
    if 'irpef_rate=' not in current_creation:
        new_fields.append('                irpef_rate=0.27')
    if 'base_shift_hours=' not in current_creation:
        new_fields.append('                base_shift_hours=6')
    if 'parameter=' not in current_creation:
        new_fields.append('                parameter=108.5')
    if 'current_year_leave=' not in current_creation:
        new_fields.append('                current_year_leave=32')
    if 'current_year_leave_used=' not in current_creation:
        new_fields.append('                current_year_leave_used=0')
    if 'previous_year_leave=' not in current_creation:
        new_fields.append('                previous_year_leave=0')
    
    if new_fields:
        # Inserisci i nuovi campi prima della parentesi di chiusura
        insert_text = ',\n' + ',\n'.join(new_fields)
        start_content = start_content[:end_pos] + insert_text + start_content[end_pos:]
        print("✅ Aggiunti campi default alla creazione utente")

# Salva start_handler aggiornato
with open('handlers/start_handler.py', 'w') as f:
    f.write(start_content)

# 3. Crea script per aggiornare utenti esistenti nel database
print("\n3️⃣ Creo script per aggiornare utenti esistenti...")

update_script = '''#!/usr/bin/env python3
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
                print(f"\\n📝 Aggiornato {user.first_name or 'Utente'} ({user.telegram_id}):")
                for change in changes:
                    print(f"   - {change}")
                updated += 1
        
        if updated > 0:
            db.commit()
            print(f"\\n✅ Aggiornati {updated} utenti")
        else:
            print("\\n✅ Tutti gli utenti hanno già i valori corretti")
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    update_existing_users()
'''

with open('update_existing_users.py', 'w') as f:
    f.write(update_script)

os.chmod('update_existing_users.py', 0o755)
print("✅ Creato script update_existing_users.py")

# 4. Commit e push
print("\n4️⃣ Commit e push...")
subprocess.run("git add database/models.py handlers/start_handler.py update_existing_users.py", shell=True)
subprocess.run('git commit -m "fix: aggiunti valori default mancanti per User (IRPEF, turno base, parametro)"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("\n📝 Modifiche applicate:")
print("1. Aggiunti default nel modello User")
print("2. Aggiornata creazione nuovi utenti con tutti i campi")
print("3. Creato script per aggiornare utenti esistenti")
print("\n🔧 Per aggiornare gli utenti esistenti nel database:")
print("python3 update_existing_users.py")
print("\n🚀 Il bot ora salverà correttamente tutti i dati!")
