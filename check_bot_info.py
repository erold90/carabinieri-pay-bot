#!/usr/bin/env python3
import subprocess

print("🔍 Verifica info bot")
print("=" * 50)

print("\n📱 Per trovare il tuo bot su Telegram:")
print("1. Apri Telegram")
print("2. Cerca @BotFather")
print("3. Invia /mybots")
print("4. Seleziona il tuo bot")
print("5. Verifica il nome utente (deve finire con 'bot')")

print("\n💡 Il nome del bot dovrebbe essere qualcosa come:")
print("- @CarabinieriPayBot")
print("- @CarabinieriBot")
print("- @PayCalcBot")
print("(o qualsiasi nome tu abbia scelto)")

print("\n🔧 Se il bot non risponde:")
print("1. Assicurati di usare il nome corretto")
print("2. Prova a inviare di nuovo /start")
print("3. Se hai cambiato token, potrebbe essere necessario:")
print("   - Bloccare il bot")
print("   - Sbloccarlo")
print("   - Inviare di nuovo /start")

print("\n📊 Per vedere se il bot riceve messaggi:")
subprocess.run("railway logs --tail 5", shell=True)

print("\n" + "=" * 50)
print("\n❓ Qual è il nome utente del tuo bot? (es: @CarabinieriPayBot)")
bot_name = input("Nome bot: ")

print(f"\n✅ Ok! Vai su Telegram e cerca: {bot_name}")
print("Poi invia /start")

print("\n🔍 Monitoro i logs per vedere se arrivano messaggi...")
print("(Premi Ctrl+C per uscire)")
subprocess.run("railway logs --tail -f", shell=True)
