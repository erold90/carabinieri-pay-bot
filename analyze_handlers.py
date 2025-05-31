#!/usr/bin/env python3
import os
import ast
import textwrap

# Directory contenente i gestori Telegram
HANDLERS_DIR = 'handlers'

# Nom­i dei tipi di handler che vogliamo rilevare
HANDLER_CLASSES = {
    'CommandHandler',
    'CallbackQueryHandler',
    'ConversationHandler'
}

def extract_docstring(node: ast.FunctionDef) -> str:
    """
    Restituisce la docstring di primo livello (solo prima riga) di una funzione, se esiste.
    """
    raw = ast.get_docstring(node)
    if not raw:
        return ''
    # Prendo solo la prima riga significativa
    first_line = raw.strip().splitlines()[0]
    return first_line

def analyze_file(path: str):
    """
    Analizza un singolo file .py:
    - Elenca tutte le funzioni con nome e prima riga di docstring (se presente).
    - Trova tutte le istanze di CommandHandler, CallbackQueryHandler e ConversationHandler
      e ne estrae il tipo + primo argomento (es. comando o callback_data).
    Stampa un breve report in console.
    """
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as e:
        print(f"⚠️  NON posso analizzare {path} (SyntaxError): {e}")
        return

    func_defs = []
    handler_insts = []

    # Scorro l'AST del file
    for node in ast.walk(tree):
        # 1) Funzioni definite
        if isinstance(node, ast.FunctionDef):
            name = node.name
            doc = extract_docstring(node)
            func_defs.append((name, doc))

        # 2) Chiamate a istanze di Handler
        if isinstance(node, ast.Call):
            # Se la chiamata è a qualcosa di .CommandHandler o semplicemente CommandHandler
            if isinstance(node.func, ast.Name) and node.func.id in HANDLER_CLASSES:
                cls_name = node.func.id
            elif isinstance(node.func, ast.Attribute) and node.func.attr in HANDLER_CLASSES:
                cls_name = node.func.attr
            else:
                continue

            # Provo a estrarre il primo argomento in forma testuale
            first_arg_repr = ''
            if node.args:
                arg0 = node.args[0]
                try:
                    # Se è una costante stringa
                    if isinstance(arg0, ast.Constant) and isinstance(arg0.value, str):
                        first_arg_repr = repr(arg0.value)
                    # Se è una lista di comandi, es. ['start', 'help']
                    elif isinstance(arg0, (ast.List, ast.Tuple)):
                        elements = []
                        for elt in arg0.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                elements.append(elt.value)
                        first_arg_repr = repr(elements)
                    else:
                        # Fallback: prendo l'espressione "as is"
                        first_arg_repr = ast.unparse(arg0) if hasattr(ast, 'unparse') else ''
                except Exception:
                    first_arg_repr = ''
            handler_insts.append((cls_name, first_arg_repr))

    # Stampo il report per questo file
    print('=' * 80)
    print(f"📄 File handler: {path}")
    print('-' * 80)

    if func_defs:
        print("🔹 Funzioni definite:")
        for name, doc in func_defs:
            if doc:
                print(f"   • {name}()    — doc: {doc}")
            else:
                print(f"   • {name}()")
    else:
        print("⚠️  Nessuna funzione trovata in questo file.")

    print()
    if handler_insts:
        print("🔹 Istanze di PTB-Handler trovate:")
        for cls_name, first_arg in handler_insts:
            if first_arg:
                print(f"   • {cls_name} (primo arg: {first_arg})")
            else:
                print(f"   • {cls_name} (argomento primo non rilevato)")
    else:
        print("ℹ️  Nessuna istanza di CommandHandler/CallbackQueryHandler/ConversationHandler trovata.")

    # Breve riepilogo automatizzato (idea di come “collabora” questo handler)
    print()
    print("🔹 Sintesi funzionamento:")
    if handler_insts:
        # Se ci sono ConversationHandler, metto in evidenza che gestisce una conversazione complessa
        conv_count = sum(1 for h in handler_insts if h[0] == 'ConversationHandler')
        if conv_count:
            print(f"   - Contiene {conv_count} ConversationHandler => Gestisce flussi multi‐step (conversazioni).")
        # Se ci sono CommandHandler
        cmd_count = sum(1 for h in handler_insts if h[0] == 'CommandHandler')
        if cmd_count:
            print(f"   - Registra {cmd_count} CommandHandler => Risponde a comandi /… specifici.")
        # CallbackQueryHandler
        cbq_count = sum(1 for h in handler_insts if h[0] == 'CallbackQueryHandler')
        if cbq_count:
            print(f"   - Utilizza {cbq_count} CallbackQueryHandler => Gestisce pulsanti inline ed eventi callback.")
    else:
        print("   - Sembra non essere un file di handler Telegram (non trova istanze di PTB-Handler).")

    print('=' * 80)
    print()

def main():
    if not os.path.isdir(HANDLERS_DIR):
        print(f"❌ Cartella '{HANDLERS_DIR}' non trovata. Esegui lo script dalla root del progetto.")
        return

    py_files = []
    for entry in os.listdir(HANDLERS_DIR):
        full_path = os.path.join(HANDLERS_DIR, entry)
        if os.path.isfile(full_path) and entry.endswith('.py'):
            py_files.append(full_path)

    if not py_files:
        print(f"⚠️  Nessun file Python (.py) trovato in '{HANDLERS_DIR}'.")
        return

    print("\n🕵️‍♂️  Inizio analisi dei file in 'handlers/'...\n")
    for fpath in sorted(py_files):
        analyze_file(fpath)

if __name__ == '__main__':
    main()
