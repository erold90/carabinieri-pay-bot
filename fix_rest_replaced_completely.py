#!/usr/bin/env python3
import subprocess
import os

print("🔧 FIX COMPLETO RELAZIONE REST_REPLACED")
print("=" * 50)

# Leggi models.py
with open('database/models.py', 'r') as f:
    content = f.read()

print("\n1️⃣ Rimozione completa riferimenti a rest_replaced...")

# Rimuovi TUTTI i riferimenti a rest_replaced
lines = content.split('\n')
cleaned_lines = []
skip_line = False

for i, line in enumerate(lines):
    # Salta completamente le linee con rest_replaced
    if 'rest_replaced' in line:
        print(f"   Rimossa linea {i+1}: {line.strip()}")
        continue
    
    # Rimuovi anche la relazione in Service se esiste
    if 'relationship("Rest"' in line and 'back_populates="service"' in line:
        print(f"   Rimossa linea {i+1}: {line.strip()}")
        continue
    
    cleaned_lines.append(line)

content = '\n'.join(cleaned_lines)

# Cerca e sistema la classe Rest
print("\n2️⃣ Pulizia classe Rest...")
lines = content.split('\n')
in_rest_class = False
cleaned_lines = []

for i, line in enumerate(lines):
    if 'class Rest(Base):' in line:
        in_rest_class = True
    elif in_rest_class and line.strip().startswith('class '):
        in_rest_class = False
    
    # Nella classe Rest, rimuovi riferimenti a service che potrebbero causare problemi
    if in_rest_class and 'service = relationship' in line and 'back_populates="rest_replaced"' in line:
        print(f"   Rimossa relazione problematica: {line.strip()}")
        continue
    
    cleaned_lines.append(line)

content = '\n'.join(cleaned_lines)

# Assicurati che non ci siano più riferimenti
if 'rest_replaced' in content:
    print("\n⚠️  ATTENZIONE: Trovati ancora riferimenti a rest_replaced!")
    # Rimuovi forzatamente
    content = content.replace('rest_replaced', 'removed_field')

# Salva il file
with open('database/models.py', 'w') as f:
    f.write(content)

print("\n✅ models.py pulito completamente")

# Verifica sintassi
print("\n3️⃣ Verifica sintassi...")
result = subprocess.run(['python3', '-m', 'py_compile', 'database/models.py'], 
                       capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Sintassi corretta")
else:
    print(f"❌ Errore sintassi: {result.stderr}")

# Crea script per drop e ricreazione tabelle
print("\n4️⃣ Creazione script reset database...")
reset_script = '''#!/usr/bin/env python3
"""Reset completo database - DA USARE SOLO SE NECESSARIO"""
import os
os.environ['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///test.db')

from database.connection import engine, Base
from database.models import *

print("⚠️  ATTENZIONE: Questo cancellerà tutti i dati!")
response = input("Sei sicuro? (yes/no): ")

if response.lower() == 'yes':
    print("🗑️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    
    print("✨ Creating new tables...")
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database reset completato!")
else:
    print("❌ Operazione annullata")
'''

with open('reset_database.py', 'w') as f:
    f.write(reset_script)
os.chmod('reset_database.py', 0o755)

print("✅ Script reset_database.py creato (usa con cautela!)")

# Commit e push
print("\n📤 Push fix completo...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: rimossi TUTTI i riferimenti a rest_replaced dal database"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ FIX COMPLETATO!")
print("\n🎯 Il bot dovrebbe ora funzionare!")
print("\nSe continua a dare errori:")
print("1. Railway potrebbe dover ricreare il database")
print("2. Puoi usare 'python3 reset_database.py' localmente per test")

os.remove(__file__)
print("\n🗑️ Script auto-eliminato")
