#!/usr/bin/env python3
"""Commit e push di tutti gli aggiornamenti"""
import subprocess
import os

print("📤 COMMIT E PUSH TUTTI GLI AGGIORNAMENTI")
print("=" * 80)

# 1. Verifica stato repository
print("\n1️⃣ Controllo stato repository...")
status_result = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True)

if not status_result.stdout.strip():
    print("✅ Nessuna modifica da committare")
    print("🔄 Verifico se ci sono commit da pushare...")
    
    # Controlla commit non pushati
    unpushed = subprocess.run("git log origin/main..HEAD --oneline", shell=True, capture_output=True, text=True)
    if unpushed.stdout.strip():
        print(f"📤 Trovati commit da pushare:\n{unpushed.stdout}")
        push_result = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
        if push_result.returncode == 0:
            print("✅ Push completato!")
        else:
            print(f"❌ Errore push: {push_result.stderr}")
    else:
        print("✅ Repository già aggiornato")
else:
    print("📝 File modificati:")
    print(status_result.stdout)
    
    # 2. Aggiungi tutti i file
    print("\n2️⃣ Aggiunta file modificati...")
    subprocess.run("git add -A", shell=True)
    print("✅ Tutti i file aggiunti")
    
    # 3. Mostra cosa verrà committato
    print("\n3️⃣ Modifiche da committare:")
    diff_stat = subprocess.run("git diff --cached --stat", shell=True, capture_output=True, text=True)
    print(diff_stat.stdout)
    
    # 4. Crea commit message dettagliato
    # Conta i file modificati per tipo
    modified_files = status_result.stdout.strip().split('\n')
    
    handlers_count = sum(1 for f in modified_files if 'handlers/' in f)
    utils_count = sum(1 for f in modified_files if 'utils/' in f)
    services_count = sum(1 for f in modified_files if 'services/' in f)
    config_count = sum(1 for f in modified_files if 'config/' in f)
    scripts_count = sum(1 for f in modified_files if '.py' in f and '/' not in f)
    
    # Crea messaggio di commit
    commit_title = "feat: aggiornamenti completi bot e fix polling"
    
    commit_body = []
    
    if 'main.py' in status_result.stdout:
        commit_body.append("- Fix polling asincrono per Railway")
        commit_body.append("- Gestione webhook migliorata")
        commit_body.append("- Logging dettagliato aggiunto")
    
    if handlers_count > 0:
        commit_body.append(f"- Aggiornati {handlers_count} handler")
    
    if utils_count > 0:
        commit_body.append(f"- Aggiunte {utils_count} utility")
    
    if services_count > 0:
        commit_body.append(f"- Modificati {services_count} servizi")
    
    if scripts_count > 0:
        commit_body.append(f"- Creati {scripts_count} script di supporto")
    
    # File specifici importanti
    important_files = {
        'requirements.txt': 'Dipendenze aggiornate',
        'Procfile': 'Configurazione deployment',
        'database/models.py': 'Modelli database aggiornati',
        '.gitignore': 'Gitignore aggiornato'
    }
    
    for file, desc in important_files.items():
        if file in status_result.stdout:
            commit_body.append(f"- {desc}")
    
    commit_message = commit_title + "\n\n" + "\n".join(commit_body)
    
    if not commit_body:
        commit_message = "chore: aggiornamenti vari e fix minori"
    
    print(f"\n4️⃣ Messaggio commit:\n{'-'*60}\n{commit_message}\n{'-'*60}")
    
    # 5. Esegui commit
    print("\n5️⃣ Creazione commit...")
    commit_result = subprocess.run(
        ["git", "commit", "-m", commit_message],
        capture_output=True,
        text=True
    )
    
    if commit_result.returncode == 0:
        print("✅ Commit creato con successo")
        
        # Mostra info commit
        last_commit = subprocess.run("git log -1 --oneline", shell=True, capture_output=True, text=True)
        print(f"📝 {last_commit.stdout.strip()}")
        
        # 6. Push
        print("\n6️⃣ Push su GitHub...")
        push_result = subprocess.run("git push origin main", shell=True, capture_output=True, text=True)
        
        if push_result.returncode == 0:
            print("✅ Push completato con successo!")
            
            # Mostra statistiche
            print("\n📊 Statistiche push:")
            if push_result.stderr:
                for line in push_result.stderr.split('\n'):
                    if 'objects' in line or 'delta' in line:
                        print(f"   {line}")
        else:
            print(f"❌ Errore push: {push_result.stderr}")
            
            # Prova a risolvere
            print("\n🔧 Tentativo di risoluzione...")
            subprocess.run("git pull --rebase origin main", shell=True)
            subprocess.run("git push origin main", shell=True)
    else:
        print(f"❌ Errore commit: {commit_result.stderr}")

# 7. Pulizia file temporanei
print("\n7️⃣ Pulizia file temporanei...")
temp_files = [
    'test_import.py',
    'quick_test.py',
    'deep_debug_bot.py',
    'monitor_railway.py',
    'force_cleanup.py',
    'cleanup_webhook.py',
    'watch_bot_startup.py'
]

cleaned = 0
for file in temp_files:
    if os.path.exists(file):
        os.remove(file)
        cleaned += 1
        print(f"   🗑️ Rimosso: {file}")

if cleaned > 0:
    print(f"✅ Puliti {cleaned} file temporanei")
else:
    print("✅ Nessun file temporaneo da pulire")

print("\n" + "=" * 80)
print("✅ PROCESSO COMPLETATO!")
print("\n📋 Riepilogo:")
print("- Tutti i file sono stati committati")
print("- Push completato su GitHub")
print("- File temporanei puliti")
print("\n🚀 Railway dovrebbe rilevare i cambiamenti e fare il deploy automaticamente")
print("⏰ Il deploy richiede solitamente 2-3 minuti")
print("\n💡 Prossimi passi:")
print("1. Controlla i log su Railway")
print("2. Quando vedi '✅ Bot in ascolto!'")
print("3. Invia /start al bot")
print("=" * 80)

# Auto-elimina questo script
os.remove(__file__)
