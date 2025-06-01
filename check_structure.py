#!/usr/bin/env python3
import os
import sys
import compileall
import ast
from pathlib import Path

######################################################################
# 1) Controllo di sintassi di tutti i .py via compileall
######################################################################
def check_syntax(root_dir):
    print("🔍 Controllo sintassi di tutti i file .py…")
    ok = compileall.compile_dir(root_dir, quiet=1)
    if ok:
        print("  ✅ Tutti i file Python compilano senza errori di sintassi.")
    else:
        print("  ❌ Sono stati trovati errori di sintassi in uno o più file.")
    return ok

######################################################################
# 2) Estrai gli import da main.py e verifica che moduli/funzioni esistano
######################################################################
def check_imports_main(main_path):
    print("\n🔍 Verifico gli import in main.py…")
    try:
        tree = ast.parse(Path(main_path).read_text(encoding='utf-8'), filename=main_path)
    except Exception as e:
        print(f"  ❌ Impossibile parsare {main_path}: {e}")
        return False

    ok = True
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            # Considero solo importFrom di interesse
            if mod.startswith("handlers.") or mod.startswith("services.") or mod.startswith("utils."):
                for alias in node.names:
                    name = alias.name
                    fullmod = mod.replace(".", os.sep) + ".py"
                    fullmod = os.path.join(os.path.dirname(main_path), fullmod) if mod.startswith("handlers") else fullmod
                    # Per handlers.* il percorso è relativo alla root: handlers/foo.py
                    # Per services.* e utils.* faccio lo stesso
                    # Es: mod="handlers.service_handler", name="new_service_command"
                    path = Path(fullmod)
                    if not path.exists():
                        print(f"  ❌ {main_path}: importa da modulo inesistente: `{mod}.{name}` → file mancante `{fullmod}`")
                        ok = False
                        continue
                    # Parso il file per verificare che esista una funzione/classe name
                    try:
                        subtree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
                    except Exception as e:
                        print(f"  ❌ Errore parsare {path}: {e}")
                        ok = False
                        continue
                    found = False
                    for subnode in ast.walk(subtree):
                        if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and subnode.name == name:
                            found = True
                            break
                    if not found:
                        print(f"  ❌ {main_path}: in `{mod}.py` manca la definizione di `{name}`")
                        ok = False
                    else:
                        print(f"  ✅ Import valido: `{mod}.{name}` esiste in {fullmod}")
    return ok

######################################################################
# 3) Controllo “file vuoti” (senza funzioni) in handlers/, services/, utils/
######################################################################
def check_empty_modules(directory):
    print(f"\n🔍 Verifico file “vuoti” in `{directory}/` (nessuna funzione definita)…")
    dirpath = Path(directory)
    if not dirpath.is_dir():
        print(f"  ❌ Cartella mancante: `{directory}/`")
        return False

    all_ok = True
    for pyfile in dirpath.glob("*.py"):
        tree = None
        try:
            tree = ast.parse(pyfile.read_text(encoding='utf-8'), filename=str(pyfile))
        except Exception as e:
            print(f"  ❌ Errore parsare {pyfile}: {e}")
            all_ok = False
            continue

        # Verifico se c’è almeno una FunctionDef o AsyncFunctionDef
        funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if not funcs:
            print(f"  ⚠️  `{pyfile}`: NON contiene funzioni (potrebbe essere vuoto o solo commenti).")
            all_ok = False
        else:
            print(f"  ✅ `{pyfile.name}` contiene {len(funcs)} funzione/e.")
    return all_ok

######################################################################
# 4) Controllo dell’esistenza delle cartelle “core” e almeno un .py
######################################################################
def check_core_dirs(root):
    print("\n🔍 Verifico presenza delle cartelle core e file .py…")
    core = ["handlers", "services", "utils"]
    all_ok = True
    for c in core:
        path = Path(root) / c
        if not path.is_dir():
            print(f"  ❌ Cartella mancante: `{c}/`")
            all_ok = False
            continue
        pyfiles = list(path.glob("*.py"))
        if not pyfiles:
            print(f"  ⚠️  `{c}/` esiste ma non contiene file `.py`.")
            all_ok = False
        else:
            print(f"  ✅ `{c}/` contiene {len(pyfiles)} file `.py`.")
    return all_ok

######################################################################
# 5) Report finale
######################################################################
def main():
    root = Path.cwd()
    overall = True

    # 1) Syntax check
    ok_syntax = check_syntax(str(root))
    if not ok_syntax:
        overall = False

    # 2) Import da main.py
    ok_imports = check_imports_main("main.py")
    if not ok_imports:
        overall = False

    # 3) File vuoti in handlers/, services/, utils/
    ok_handlers = check_empty_modules("handlers")
    ok_services = check_empty_modules("services")
    ok_utils = check_empty_modules("utils")
    if not (ok_handlers and ok_services and ok_utils):
        overall = False

    # 4) Controllo cartelle core
    ok_core = check_core_dirs(root)
    if not ok_core:
        overall = False

    print("\n====== REPORT FINALE ======")
    if overall:
        print("🎉 Tutti i controlli di struttura sono passati! Il progetto è coerente.")
        sys.exit(0)
    else:
        print("❌ Alcuni controlli di struttura non sono stati superati. Rivedi i messaggi sopra.")
        sys.exit(1)

if __name__ == "__main__":
    main()
