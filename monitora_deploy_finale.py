#!/usr/bin/env python3
import subprocess
import time
import sys

print("🚀 MONITORAGGIO DEPLOY FINALE")
print("=" * 50)

# 1. Mostra stato git
print("\n1️⃣ Stato repository:")
subprocess.run("git log --oneline -5", shell=True)

print("\n2️⃣ File modificati di recente:")
subprocess.run("ls -la *.py | head -10", shell=True)

# 3. Verifica Railway
print("\n3️⃣ Stato Railway:")
print("Controlla il deploy su: https://railway.app/dashboard")

# 4. Istruzioni test
print("\n" + "=" * 50)
print("📱 ISTRUZIONI PER IL TEST COMPLETO")
print("=" * 50)

print("""
1. APRI TELEGRAM e cerca: @CC_pay2_bot

2. INVIA: /start
   ✓ Dovrebbe apparire il menu principale
   ✓ I messaggi vecchi dovrebbero essere eliminati

3. TESTA I PULSANTI PRINCIPALI:
   
   🆕 Nuovo Servizio:
   - Seleziona data (oggi/ieri)
   - Inserisci orario (es: 8:30)
   - Scegli tipo servizio
   
   ⏰ Gestione Straordinari:
   - Visualizza riepilogo
   - Controlla ore accumulate
   
   📋 Fogli Viaggio:
   - Visualizza FV in attesa
   - Registra pagamento
   
   🏖️ Gestione Licenze:
   - Controlla giorni residui
   - Inserisci nuova licenza
   
   ⚙️ Impostazioni:
   - Modifica grado
   - Cambia aliquota IRPEF
   - Aggiorna comando

4. VERIFICA CLEAN CHAT:
   - Dopo alcuni messaggi, i vecchi dovrebbero sparire
   - Dovrebbero rimanere solo gli ultimi 3

5. SE UN PULSANTE NON FUNZIONA:
   - Apparirà "Funzione in sviluppo"
   - Usa /start per tornare al menu

""")

# 5. Monitoraggio logs
print("=" * 50)
choice = input("\nVuoi monitorare i logs in tempo reale? (s/n): ")

if choice.lower() == 's':
    print("\n📊 LOGS IN TEMPO REALE")
    print("(Premi Ctrl+C per uscire)")
    print("-" * 50)
    
    try:
        subprocess.run("railway logs -f", shell=True)
    except KeyboardInterrupt:
        print("\n\n✅ Monitoraggio interrotto")

print("\n" + "=" * 50)
print("🎉 DEPLOYMENT COMPLETATO!")
print("\nIl bot CarabinieriPayBot dovrebbe essere completamente funzionante!")
print("\n⚠️ Se trovi problemi:")
print("1. Controlla i logs: railway logs --tail 50")
print("2. Verifica le variabili: railway variables")
print("3. Riavvia se necessario: railway restart")
