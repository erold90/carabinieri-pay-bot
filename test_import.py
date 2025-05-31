#!/usr/bin/env python3
import os
import sys

print("🧪 Test import main.py...")
try:
    # Aggiungi la directory corrente al path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Prova a importare main
    import main
    print("✅ Import riuscito!")
    
    # Verifica che le funzioni esistano
    funcs = ['start_command', 'hello_command', 'ping_command']
    for func in funcs:
        if hasattr(main, func):
            print(f"✅ Funzione {func} trovata")
        else:
            print(f"❌ Funzione {func} non trovata")
            
except IndentationError as e:
    print(f"❌ Errore indentazione: {e}")
except ImportError as e:
    print(f"❌ Errore import: {e}")
except Exception as e:
    print(f"❌ Errore: {e}")
