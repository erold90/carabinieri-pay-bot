#!/usr/bin/env python3
import subprocess
import sys
from datetime import datetime

def run_command(cmd, shell=True):
    """Esegue comando e gestisce output"""
    try:
        result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("🤖 CarabinieriPayBot - Git Automation")
    print("=" * 50)
    
    # 1. Check status
    print("\n📊 Stato repository:")
    success, stdout, stderr = run_command("git status --porcelain")
    
    if not success:
        print(f"❌ Errore: {stderr}")
        sys.exit(1)
    
    if not stdout.strip():
        print("✅ Nessuna modifica da committare")
        
        # Check if there are commits to push
        success, stdout, _ = run_command("git log origin/main..HEAD --oneline")
        if stdout.strip():
            print(f"\n📤 Commit da pushare:\n{stdout}")
            push = input("\nVuoi pushare? (s/n): ").lower()
            if push == 's':
                print("\n🚀 Push in corso...")
                success, stdout, stderr = run_command("git push origin main")
                if success:
                    print("✅ Push completato!")
                else:
                    print(f"❌ Errore push: {stderr}")
        else:
            print("✅ Repository aggiornato con origin")
        return
    
    # 2. Show changes
    print("\n📝 File modificati:")
    print(stdout)
    
    # 3. Git add
    add_all = input("\nAggiungere tutti i file? (s/n): ").lower()
    
    if add_all == 's':
        run_command("git add .")
        print("✅ File aggiunti")
    else:
        print("\nSeleziona file da aggiungere:")
        files = stdout.strip().split('\n')
        for i, file in enumerate(files):
            print(f"{i+1}. {file}")
        
        selections = input("\nInserisci numeri separati da virgola: ").split(',')
        for sel in selections:
            try:
                idx = int(sel.strip()) - 1
                if 0 <= idx < len(files):
                    filename = files[idx].split()[-1]
                    run_command(f"git add {filename}")
                    print(f"✅ Aggiunto: {filename}")
            except:
                pass
    
    # 4. Commit message
    print("\n💬 Tipo di commit:")
    print("1. feat: nuova funzionalità")
    print("2. fix: correzione bug")
    print("3. docs: documentazione")
    print("4. style: formattazione")
    print("5. refactor: refactoring codice")
    print("6. test: aggiunta test")
    print("7. chore: manutenzione")
    
    commit_type = input("\nScegli (1-7): ")
    
    types = {
        '1': 'feat',
        '2': 'fix',
        '3': 'docs',
        '4': 'style',
        '5': 'refactor',
        '6': 'test',
        '7': 'chore'
    }
    
    prefix = types.get(commit_type, 'update')
    
    message = input(f"\nMessaggio commit ({prefix}:): ")
    full_message = f"{prefix}: {message}"
    
    # 5. Commit
    success, stdout, stderr = run_command(f'git commit -m "{full_message}"')
    
    if success:
        print(f"\n✅ Commit creato: {full_message}")
    else:
        print(f"❌ Errore commit: {stderr}")
        sys.exit(1)
    
    # 6. Push
    push = input("\nVuoi pushare su GitHub? (s/n): ").lower()
    
    if push == 's':
        print("\n🚀 Push in corso...")
        success, stdout, stderr = run_command("git push origin main")
        
        if success:
            print("✅ Push completato!")
            print("\n🎉 Aggiornamento completato con successo!")
        else:
            if "no upstream branch" in stderr:
                print("⚠️  Branch non collegato. Provo con --set-upstream...")
                success, stdout, stderr = run_command("git push --set-upstream origin main")
                if success:
                    print("✅ Push completato e branch collegato!")
                else:
                    print(f"❌ Errore: {stderr}")
            else:
                print(f"❌ Errore push: {stderr}")

if __name__ == "__main__":
    main()
