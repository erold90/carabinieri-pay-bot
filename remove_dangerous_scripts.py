#!/usr/bin/env python3
import subprocess
import os

print("🔧 RIMOZIONE SCRIPT PERICOLOSI")
print("=" * 50)

# Script da rimuovere
dangerous_scripts = [
    'reset_database.py',
    'recreate_db.py'
]

for script in dangerous_scripts:
    if os.path.exists(script):
        os.remove(script)
        print(f"✅ Rimosso: {script}")
        subprocess.run(f"git rm {script}", shell=True)

# Commit
subprocess.run("git add -A", shell=True)
subprocess.run('git commit -m "security: rimossi script pericolosi di reset database"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n✅ Script pericolosi rimossi!")

import os
os.remove(__file__)
