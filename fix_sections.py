#!/usr/bin/env python3
import os
import re
import subprocess
import sys
from textwrap import dedent

# ------------------------------------------------------------------------------
# Script di verifica e autogenerazione delle sezioni del bot:
#
# 1) Per ogni sezione (setup, service, overtime, leave, rest, travel_sheet):
#    - Controlla che esista il file handler appropriato in handlers/.
#    - Controlla che all’interno di quel file esista la funzione comando (es. overtime_command).
#      Se manca, la genera come “stub” che risponde “🚧 Funzionalità non implementata”.
#    - Controlla che main.py importi quella funzione. Se manca, aggiunge:
#         from handlers.<modulo> import <funzione>
#    - Controlla che main.py registri il comando via
#         application.add_handler(CommandHandler("comando", funzione))
#      (oppure ConversationHandler). Se manca, lo aggiunge prima di
#      application.run_polling() (o application.start()).
#
# 2) Se ha fatto almeno una modifica, esegue:
#       git add .
#       git commit -m "fix: aggiorno sezioni handler mancanti/stub"
#       git push origin main
#
# 3) Si auto-elimina (os.remove(__file__)).
#
# Per eseguirlo:
#   chmod +x fix_sections.py
#   python3 fix_sections.py
# ------------------------------------------------------------------------------

# Mappatura delle sezioni verso file, funzione e righe da inserire in main.py
SECTIONS = {
    'setup': {
        'file': 'handlers/setup_handler.py',
        'func': 'setup_conversation_handler',
        # Si registra direttamente il ConversationHandler
        'add_cmd': 'application.add_handler(setup_conversation_handler)',
        'import_stmt': 'from handlers.setup_handler import setup_conversation_handler'
    },
    'service': {
        'file': 'handlers/service_handler.py',
        'func': 'new_service_command',
        'add_cmd': 'application.add_handler(CommandHandler("nuovo", new_service_command))\n    application.add_handler(CommandHandler("scorta", new_service_command))',
        'import_stmt': 'from handlers.service_handler import new_service_command'
    },
    'overtime': {
        'file': 'handlers/overtime_handler.py',
        'func': 'overtime_command',
        'add_cmd': 'application.add_handler(CommandHandler("straordinari", overtime_command))',
        'import_stmt': 'from handlers.overtime_handler import overtime_command'
    },
    'leave': {
        'file': 'handlers/leave_handler.py',
        'func': 'leave_command',
        'add_cmd': dedent("""\
            application.add_handler(CommandHandler("licenze", leave_command))
            application.add_handler(CommandHandler("nuova_licenza", add_leave_command))
            application.add_handler(CommandHandler("pianifica_licenze", plan_leave_command))
        """).strip(),
        'import_stmt': 'from handlers.leave_handler import leave_command, add_leave_command, plan_leave_command'
    },
    'rest': {
        'file': 'handlers/rest_handler.py',
        'func': 'rest_command',
        'add_cmd': 'application.add_handler(CommandHandler("riposi", rest_command))',
        'import_stmt': 'from handlers.rest_handler import rest_command'
    },
    'travel_sheet': {
        'file': 'handlers/travel_sheet_handler.py',
        'func': 'travel_sheets_command',
        'add_cmd': 'application.add_handler(CommandHandler("fv", travel_sheets_command))',
        'import_stmt': 'from handlers.travel_sheet_handler import travel_sheets_command'
    }
}

MAIN_PY = 'main.py'

def ensure_function_in_module(module_path: str, func_name: str) -> bool:
    """
    Controlla se in module_path esiste una riga “async def func_name(…):”.
    Se non esiste, aggiunge alla fine del file un semplice stub che risponde “🚧 Funzionalità non implementata”.
    Ritorna True se la funzione già esiste, False se creata dallo script.
    """
    if not os.path.isfile(module_path):
        print(f"    ❌ File handler mancante: {module_path}")
        return False

    with open(module_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Ricerca di "async def func_name("
    pattern = rf'^\s*async\s+def\s+{re.escape(func_name)}\s*\('
    if re.search(pattern, content, flags=re.MULTILINE):
        print(f"    ✔️ Funzione `{func_name}` già presente in {module_path}")
        return True

    # Aggiungo lo stub alla fine
    stub = dedent(f"""

        # ------------------------------
        # Stub autogenerato da fix_sections.py
        # ------------------------------
        async def {func_name}(update, context):
            \"\"\"Funzione `{func_name}` generata automaticamente perché mancava.\"\"\"
            await update.message.reply_text("🚧 La funzionalità `{func_name}` non è ancora implementata.")
    """)
    with open(module_path, 'a', encoding='utf-8') as f:
        f.write(stub)

    print(f"    ➕ Creato stub `{func_name}` in {module_path}")
    return False

def ensure_import_in_main(import_stmt: str) -> bool:
    """
    Verifica se 'import_stmt' esiste già in main.py.
    Se manca, lo aggiunge subito dopo l’ultimo blocco di import (linee che iniziano con import/ from).
    Ritorna True se già presente, False se aggiunto ora.
    """
    if not os.path.isfile(MAIN_PY):
        print("    ❌ main.py non trovato.")
        sys.exit(1)

    with open(MAIN_PY, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Se la riga di import esatta è già presente:
    if any(import_stmt.strip() == line.strip() for line in lines):
        print(f"    ✔️ Import già presente: `{import_stmt}`")
        return True

    # Trovo ultima riga di import
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            insert_idx = i + 1

    lines.insert(insert_idx, import_stmt + '\n')
    with open(MAIN_PY, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"    ➕ Aggiunto import in main.py: `{import_stmt}`")
    return False

def ensure_addhandler_in_main(add_cmd: str) -> bool:
    """
    Verifica se 'add_cmd' (anche multilinea) è già presente in main.py.
    Se manca, lo aggiunge subito prima di application.run_polling() o application.start().
    Ritorna True se già presente, False se aggiunto ora.
    """
    with open(MAIN_PY, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    joined = "".join(lines)
    if add_cmd in joined:
        print(f"    ✔️ Rilevata riga add_handler già esistente:\n      {add_cmd.replace(chr(10), format(chr(10)+'      '))}")
        return True

    # Trovo dove inserire: prima di run_polling(), start() o updater.start_polling
    insert_idx = None
    for i, line in enumerate(lines):
        if 'application.run_polling' in line or 'application.start(' in line or 'updater.start_polling' in line:
            insert_idx = i
            break
    if insert_idx is None:
        insert_idx = len(lines)

    block = []
    for subline in add_cmd.splitlines():
        block.append('    ' + subline.rstrip() + '\n')

    lines[insert_idx:insert_idx] = block
    with open(MAIN_PY, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"    ➕ Aggiunta riga add_handler in main.py:\n      {add_cmd.replace(chr(10), format(chr(10)+'      '))}")
    return False

if __name__ == '__main__':
    print()
    print("🔍 Verifica e autogenerazione sezioni handler...")
    print("——————————————————————————————————————————————")
    any_changes = False

    for section, data in SECTIONS.items():
        mod_path = data['file']
        func_name = data['func']
        import_stmt = data['import_stmt']
        add_cmd = data['add_cmd']

        print(f"\n📂 Sezione “{section}”")
        print(f"  – File atteso: {mod_path}")

        # 1) Controllo/esistenza del file
        if not os.path.isfile(mod_path):
            print(f"    ❌ Il file handler non esiste. Crealo manualmente: {mod_path}")
            continue
        else:
            print(f"    📄 File esiste ✔️")

        # 2) Controllo/esistenza funzione comando nel modulo
        existed = ensure_function_in_module(mod_path, func_name)
        if not existed:
            any_changes = True

        # 3) Controllo/esistenza dell’import in main.py
        ok_import = ensure_import_in_main(import_stmt)
        if not ok_import:
            any_changes = True

        # 4) Controllo/esistenza di add_handler in main.py
        ok_add = ensure_addhandler_in_main(add_cmd)
        if not ok_add:
            any_changes = True

    # Se ho fatto modifiche, committale e pusha
    if any_changes:
        print("\n📤 Effettuo git add/commit/push delle modifiche…")
        try:
            subprocess.run("git add .", shell=True, check=True)
            subprocess.run('git commit -m "fix: aggiorno sezioni handler mancanti/stub"', shell=True, check=True)
            subprocess.run("git push origin main", shell=True, check=True)
            print("✅ Commit e push eseguiti.")
        except subprocess.CalledProcessError as e:
            print(f"❌ Errore durante commit/push: {e}")
    else:
        print("\nℹ️  Nessuna modifica da committare.")

    # Auto-elimino lo script stesso
    print("\n🗑️ Auto-eliminazione di fix_sections.py.")
    try:
        os.remove(__file__)
        print("✅ Script eliminato correttamente.")
    except Exception as e:
        print(f"❌ Errore durante rimozione: {e}", file=sys.stderr)

    print("\n🚀 Tutto fatto! Railway rileverà il nuovo deploy automaticamente.")
    print()
