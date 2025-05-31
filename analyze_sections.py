#!/usr/bin/env python3
import os
import ast
import textwrap

# Mappa delle "sezioni" del bot verso i rispettivi file handler
SECTIONS = {
    'setup'        : 'handlers/setup_handler.py',
    'service'      : 'handlers/service_handler.py',
    'overtime'     : 'handlers/overtime_handler.py',
    'leave'        : 'handlers/leave_handler.py',
    'rest'         : 'handlers/rest_handler.py',
    'travel_sheet' : 'handlers/travel_sheet_handler.py',
    # Se vuoi aggiungere altre sezioni, basta estendere questo dizionario
}

# Quali tipi di PTB-Handler consideriamo "validi"
HANDLER_CLASSES = {'CommandHandler', 'CallbackQueryHandler', 'ConversationHandler'}

def has_ptb_handler(filepath: str) -> bool:
    """
    Ritorna True se all'interno di 'filepath' (un file .py) è presente
    almeno una chiamata a CommandHandler, CallbackQueryHandler o ConversationHandler.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
    except FileNotFoundError:
        return False

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        # Se c'è un errore di sintassi, consideriamo "False" (non affidabile)
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            # Caso 1: nome semplice, es. CommandHandler(...)
            if isinstance(func, ast.Name) and func.id in HANDLER_CLASSES:
                return True
            # Caso 2: attributo, es. telegram.ext.CommandHandler(...)
            if isinstance(func, ast.Attribute) and func.attr in HANDLER_CLASSES:
                return True
    return False

def main():
    print("\n🔍 Verifica delle sezioni del bot e dei relativi handler\n")
    all_ok = True

    for section, path in SECTIONS.items():
        print(f"— Sezione '{section}':")
        if not os.path.isfile(path):
            print(f"    ❌ File non trovato: {path}")
            all_ok = False
            continue

        print(f"    📄 File rilevato: {path}")
        if has_ptb_handler(path):
            print("    ✅ Presente almeno un handler Telegram (Command/Callback/Conversation).")
        else:
            print("    ⚠️  Nessun CommandHandler/CallbackQueryHandler/ConversationHandler trovato.")
            all_ok = False

    print("\n" + ("🎉 Tutte le sezioni sono correttamente implementate!" if all_ok
                   else "⚠️  Alcune sezioni mancano o non contengono handler. Controlla i warning sopra."))
    print()

if __name__ == '__main__':
    main()
