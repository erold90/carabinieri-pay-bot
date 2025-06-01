#!/usr/bin/env python3
import subprocess

print("🔧 Fix avvio bot e gestione event loop")
print("=" * 50)

# 1. Prima rimuoviamo eventuali webhook
print("🌐 Rimozione webhook...")
subprocess.run("python3 railway_cleanup.py", shell=True)

# 2. Modifichiamo main.py per gestire correttamente l'event loop
with open('main.py', 'r') as f:
    content = f.read()

# Rimuovi la duplicazione del codice di inizializzazione
# Cerca se ci sono inizializzazioni duplicate
init_count = content.count('init_db()')
if init_count > 1:
    print(f"⚠️ Trovate {init_count} chiamate a init_db(), rimozione duplicati...")
    # Trova e rimuovi duplicati
    lines = content.split('\n')
    new_lines = []
    seen_init = False
    skip_next = 0
    
    for i, line in enumerate(lines):
        if skip_next > 0:
            skip_next -= 1
            continue
            
        if 'init_db()' in line and seen_init:
            # Salta questa sezione
            j = i
            while j < len(lines) and not lines[j].strip().startswith('# Create the Application'):
                j += 1
            skip_next = j - i - 1
            continue
        elif 'init_db()' in line:
            seen_init = True
            
        new_lines.append(line)
    
    content = '\n'.join(new_lines)

# Sostituisci il blocco finale con una versione corretta
final_block = '''if __name__ == '__main__':
    import asyncio
    import sys
    
    try:
        # Per Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # Prova a usare asyncio.run
        asyncio.run(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            # Railway potrebbe avere un event loop già attivo
            print("⚠️ Event loop già attivo, uso alternativo...")
            loop = asyncio.get_event_loop()
            loop.create_task(main())
        else:
            raise
    except KeyboardInterrupt:
        print("\\n👋 Bot fermato dall'utente")
    except Exception as e:
        print(f"❌ Errore critico: {e}")
        import traceback
        traceback.print_exc()'''

# Trova l'inizio del blocco if __name__
if_main_pos = content.find("if __name__ == '__main__':")
if if_main_pos != -1:
    content = content[:if_main_pos] + final_block
else:
    content += '\n\n' + final_block

# Salva main.py
with open('main.py', 'w') as f:
    f.write(content)

print("✅ main.py aggiornato")

# 3. Creiamo uno script per killare processi bot duplicati
with open('kill_duplicate_bots.py', 'w') as f:
    f.write('''#!/usr/bin/env python3
import os
import signal
import psutil

print("🔍 Ricerca processi Python duplicati...")

current_pid = os.getpid()
python_processes = []

for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['name'] and 'python' in proc.info['name'].lower():
            if proc.info['cmdline'] and any('main.py' in arg for arg in proc.info['cmdline']):
                if proc.info['pid'] != current_pid:
                    python_processes.append(proc.info['pid'])
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

if python_processes:
    print(f"⚠️ Trovati {len(python_processes)} processi bot duplicati")
    for pid in python_processes:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"✅ Terminato processo {pid}")
        except:
            print(f"❌ Non posso terminare {pid}")
else:
    print("✅ Nessun processo duplicato trovato")
''')

# 4. Aggiungiamo psutil a requirements.txt se non presente
with open('requirements.txt', 'r') as f:
    requirements = f.read()

if 'psutil' not in requirements:
    with open('requirements.txt', 'a') as f:
        f.write('\npsutil==5.9.6\n')
    print("✅ Aggiunto psutil a requirements.txt")

# 5. Modifichiamo il ConversationHandler per rimuovere per_message=True che causa problemi
print("\n🔧 Fix ConversationHandler...")

# Fix service_handler.py
with open('handlers/service_handler.py', 'r') as f:
    service_content = f.read()

service_content = service_content.replace(
    'ConversationHandler(per_message=True,',
    'ConversationHandler('
)

with open('handlers/service_handler.py', 'w') as f:
    f.write(service_content)

# Fix setup_handler.py
with open('handlers/setup_handler.py', 'r') as f:
    setup_content = f.read()

setup_content = setup_content.replace(
    'ConversationHandler(per_message=True,',
    'ConversationHandler('
)

with open('handlers/setup_handler.py', 'w') as f:
    f.write(setup_content)

print("✅ Rimosso per_message=True dai ConversationHandler")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "fix: risolto event loop e bot duplicati, rimosso per_message"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n✅ Fix completato!")
print("🚀 Il bot dovrebbe avviarsi correttamente ora")
print("\n⚠️ IMPORTANTE: Attendi che Railway completi il deploy")
print("   poi controlla i log per verificare che non ci siano più errori")

import os
os.remove(__file__)
