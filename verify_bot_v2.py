#!/usr/bin/env python3
import os
import sys
import ast

# Provo a importare SQLAlchemy; se non c’è, lo segnalo come avviso
try:
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.pool import NullPool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

######################################################################
# 1) VARIABILI D'AMBIENTE (⚠️ solo avviso)
######################################################################
def check_env_vars():
    print("\n🔍 Controllo variabili d’ambiente…")
    missing = []
    for var in ("TELEGRAM_TOKEN", "DATABASE_URL"):
        if not os.getenv(var):
            missing.append(var)
    if missing:
        print(f"⚠️ Mancano le seguenti variabili d’ambiente: {', '.join(missing)}")
        return False
    else:
        print("✅ Tutte le variabili d’ambiente obbligatorie sono presenti.")
        return True

######################################################################
# 2) CONNESSIONE DB E PRESENZA TABELLE (⚠️ avviso, non fallisce se SQLAlchemy non installato)
######################################################################
EXPECTED_TABLES = {"users", "services", "overtimes", "travel_sheets", "leaves", "rests"}

def check_database():
    print("\n🔍 Verifica connessione al database e tabelle…")
    url = os.getenv("DATABASE_URL")
    if not url:
        print("⚠️ DATABASE_URL non è impostata: salto il controllo DB.")
        return False

    if not SQLALCHEMY_AVAILABLE:
        print("⚠️ SQLAlchemy non installato: impossibile verificare il database.")
        return False

    try:
        engine = create_engine(url, poolclass=NullPool)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        missing = EXPECTED_TABLES - tables
        if missing:
            print(f"❌ Mancano le tabelle nel database: {', '.join(missing)}")
            return False
        else:
            print("✅ Tutte le tabelle obbligatorie esistono nel database.")
            return True
    except Exception as e:
        print(f"⚠️ Impossibile connettersi al database: {e}")
        return False

######################################################################
# 3) SINTASSI E PRESENZA FUNZIONE (non istanza) nei moduli di handlers/
######################################################################
# Mappatura delle sezioni verso il file e la funzione attesa
SECTIONS = {
    'setup': {
        'file': 'handlers/setup_handler.py',
        'func': 'setup_conversation_handler'
    },
    'service': {
        'file': 'handlers/service_handler.py',
        'func': 'new_service_command'
    },
    'overtime': {
        'file': 'handlers/overtime_handler.py',
        'func': 'overtime_command'
    },
    'leave': {
        'file': 'handlers/leave_handler.py',
        'func': 'leave_command'
    },
    'rest': {
        'file': 'handlers/rest_handler.py',
        'func': 'rest_command'
    },
    'travel_sheet': {
        'file': 'handlers/travel_sheet_handler.py',
        'func': 'travel_sheets_command'
    }
}

def parse_file_no_syntax(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, path, "exec")
        return True, None
    except Exception as e:
        return False, str(e)

def function_exists_in_module(path, func_name):
    """
    Verifica che in path (.py) sia definita 'def func_name(' o 'async def func_name('.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        return False

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == func_name:
                return True
        if isinstance(node, ast.AsyncFunctionDef):
            if node.name == func_name:
                return True
    return False

def check_handlers():
    print("\n🔍 Verifica moduli handlers (sintassi + presenza funzione attesa)…")
    all_ok = True

    for section, info in SECTIONS.items():
        path = info['file']
        func = info['func']
        print(f"\n— Sezione '{section}': modulo atteso: {path}")

        # 3.1) Controllo esistenza file
        if not os.path.isfile(path):
            print(f"❌ File non trovato: {path}")
            all_ok = False
            continue
        else:
            print("  📄 File esiste.")

        # 3.2) Controllo sintassi
        ok_syntax, err = parse_file_no_syntax(path)
        if not ok_syntax:
            print(f"❌ Sintassi non valida in {path}: {err}")
            all_ok = False
            continue
        else:
            print("  ✅ Sintassi OK.")

        # 3.3) Controllo presenza di func
        if function_exists_in_module(path, func):
            print(f"  ✅ Trovata definizione di `{func}` in {path}.")
        else:
            print(f"❌ Funzione `{func}` mancante in {path}.")
            all_ok = False

    return all_ok

######################################################################
# 4) CONTROLLO DI main.py: import e add_handler (parziale) per ciascuna sezione
######################################################################
# Mappatura con import_stmt completo e frammento di add_handler
SECTION_MAIN_CHECK = {
    'setup': {
        'import_stmt': 'from handlers.setup_handler import setup_conversation_handler',
        'add_cmd': 'application.add_handler(setup_conversation_handler)'
    },
    'service': {
        'import_stmt': 'from handlers.service_handler import new_service_command',
        'add_cmd': 'CommandHandler("nuovo", new_service_command)'
    },
    'overtime': {
        'import_stmt': 'from handlers.overtime_handler import overtime_command',
        'add_cmd': 'CommandHandler("straordinari", overtime_command)'
    },
    'leave': {
        'import_stmt': 'from handlers.leave_handler import leave_command',
        'add_cmd': 'CommandHandler("licenze", leave_command)'
    },
    'rest': {
        'import_stmt': 'from handlers.rest_handler import rest_command',
        'add_cmd': 'CommandHandler("riposi", rest_command)'
    },
    'travel_sheet': {
        'import_stmt': 'from handlers.travel_sheet_handler import travel_sheets_command',
        'add_cmd': 'CommandHandler("fv", travel_sheets_command)'
    }
}

def check_main_py():
    print("\n🔍 Verifica di 'main.py' per import e add_handler…")
    MAIN = "main.py"
    if not os.path.isfile(MAIN):
        print("❌ File 'main.py' non trovato.")
        return False

    try:
        with open(MAIN, "r", encoding="utf-8") as f:
            lines = f.readlines()
            joined = "".join(lines)
    except Exception as e:
        print(f"❌ Impossibile leggere main.py: {e}")
        return False

    all_ok = True
    for section, info in SECTION_MAIN_CHECK.items():
        imp = info['import_stmt']
        add = info['add_cmd']

        if imp in joined:
            print(f"  ✅ import per '{section}' trovato: `{imp}`")
        else:
            print(f"  ❌ import per '{section}' MANCANTE: `{imp}`")
            all_ok = False

        if add in joined:
            print(f"  ✅ add_handler per '{section}' trovato (parziale): `{add}`")
        else:
            print(f"  ❌ add_handler per '{section}' MANCANTE: `{add}`")
            all_ok = False

    # Verifico anche la sintassi generale di main.py
    ok_syntax, err = parse_file_no_syntax(MAIN)
    if not ok_syntax:
        print(f"\n❌ main.py contiene errori di sintassi: {err}")
        return False
    else:
        print("  ✅ Sintassi di main.py OK.")

    return all_ok

######################################################################
# 5) REPORT FINALE E EXIT CODE
######################################################################
def main():
    print("\n====== INIZIO CHECK BOT ======")
    overall_ok = True

    env_ok = check_env_vars()
    db_ok = check_database()
    handlers_ok = check_handlers()
    main_ok = check_main_py()

    print("\n====== RISULTATO FINALE ======")
    # Variabili e DB sono avvisi, non errori fatali per eseguire il bot in locale.
    if not env_ok:
        print("⚠️  Alcune variabili d’ambiente mancanti, ma i controlli proseguono.")
    if not db_ok:
        print("⚠️  Controllo database fallito o non disponibile, ma i controlli proseguono.")
    if not handlers_ok or not main_ok:
        print("❌ ALMENO UN CONTROLLO CRITICO È FALLITO. Il bot NON funzionerà correttamente.")
        sys.exit(1)

    print("🎉 TUTTI I CONTROLLI ESSENZIALI SONO PASSATI!")
    print("Il bot è pronto: variabili, moduli e main.py sono a posto.")
    sys.exit(0)

if __name__ == "__main__":
    main()
