#!/usr/bin/env python3
import subprocess
import time

print("🔍 Verifica stato bot dopo fix")
print("=" * 50)

# Mostra ultimi commit
print("\n📝 Ultimi commit:")
subprocess.run("git log --oneline -5", shell=True)

print("\n⏰ Attendere il deploy su Railway...")
print("   Il deploy richiede circa 2-3 minuti")
print("\n📱 Quando pronto, testa questi comandi:")
print("   /start - Dovrebbe mostrare il menu principale")
print("   /nuovo - Registrazione nuovo servizio")
print("   /impostazioni - Configurazione profilo")
print("\n⚠️ Se ricevi errori, esegui: python3 check_errors.py")
