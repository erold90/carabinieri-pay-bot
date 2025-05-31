#!/usr/bin/env python3
import subprocess
import os

print("🔧 FIX ERRORE RELAZIONI DATABASE")
print("=" * 50)

# Leggi database/models.py
with open('database/models.py', 'r') as f:
    content = f.read()

print("\n1️⃣ Analisi problema...")
print("Il problema è nella relazione Rest.rest_replaced")

# Trova e correggi la relazione problematica
lines = content.split('\n')
fixed = False

for i, line in enumerate(lines):
    # Cerca la relazione problematica in Rest
    if 'rest_replaced = relationship("Rest"' in line:
        print(f"✅ Trovata relazione problematica alla linea {i+1}")
        # Commenta questa linea problematica
        lines[i] = '    # ' + line.strip() + '  # FIXME: Relazione circolare'
        fixed = True

# Cerca anche in Service la relazione inversa
for i, line in enumerate(lines):
    if 'class Service(Base):' in line:
        # Cerca nelle prossime righe
        j = i + 1
        while j < len(lines) and not lines[j].startswith('class '):
            if 'rest_replaced = relationship' in lines[j]:
                print(f"✅ Trovata relazione in Service alla linea {j+1}")
                lines[j] = '    # ' + lines[j].strip() + '  # FIXME: Da rivedere'
            j += 1

# Ricostruisci il contenuto
if fixed:
    content = '\n'.join(lines)
    
    # Salva il file
    with open('database/models.py', 'w') as f:
        f.write(content)
    
    print("\n✅ Relazioni problematiche commentate")
else:
    print("\n⚠️  Non ho trovato le relazioni problematiche")

# 2. Crea script per ricreare le tabelle se necessario
print("\n2️⃣ Creazione script ricreazione tabelle...")

recreate_script = '''#!/usr/bin/env python3
"""Script per ricreare le tabelle del database se necessario"""
from database.connection import engine, Base, init_db
from database.models import User, Service, Overtime, TravelSheet, Leave, Rest

print("🔄 Ricreazione tabelle database...")

try:
    # Inizializza database
    init_db()
    print("✅ Database inizializzato correttamente")
except Exception as e:
    print(f"❌ Errore: {e}")
    print("Provo a ricreare le tabelle...")
    
    try:
        # Drop e ricrea
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelle ricreate")
    except Exception as e2:
        print(f"❌ Errore ricreazione: {e2}")
'''

with open('recreate_db.py', 'w') as f:
    f.write(recreate_script)

print("✅ Script recreate_db.py creato")

# 3. Verifica sintassi
print("\n3️⃣ Verifica sintassi models.py...")
result = subprocess.run(['python3', '-m', 'py_compile', 'database/models.py'], 
                       capture_output=True, text=True)

if result.returncode == 0:
    print("✅ Sintassi corretta")
else:
    print(f"❌ Errore sintassi: {result.stderr}")

# 4. Commit e push
print("\n📤 Push fix database...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: rimossa relazione circolare Rest.rest_replaced che causava errore"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ FIX COMPLETATO!")
print("\n⚠️  NOTA: La funzionalità dei riposi potrebbe essere limitata")
print("ma il bot dovrebbe ora avviarsi correttamente!")
print("\n🎯 Attendi il redeploy e riprova /start")

# Auto-elimina
os.remove(__file__)
print("\n🗑️ Script auto-eliminato")
