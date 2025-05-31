#!/usr/bin/env python3
import os
import subprocess

print("🔧 Aggiornamento .gitignore per escludere file e cartelle inutili")
print("=" * 60)

gitignore_path = '.gitignore'

# Se .gitignore non esiste, lo crea vuoto
if not os.path.exists(gitignore_path):
    open(gitignore_path, 'w').close()

with open(gitignore_path, 'r', encoding='utf-8') as f:
    existing = set([l.rstrip() for l in f.readlines()])

# Pattern da aggiungere
patterns = [
    "# macOS",
    ".DS_Store",
    "",
    "# Python bytecode",
    "__pycache__/",
    "*.pyc",
    "",
    "# Database fallback (locale)",
    "fallback.db",
    "",
    "# Environment",
    ".env",
    "",
    "# Railway / Heroku / altri",
    "runtime.txt",
    ".deploy_check",
    "",
    "# Cartelle di test / output",
    "tests/__pycache__/",
]

with open(gitignore_path, 'a', encoding='utf-8') as f:
    for pat in patterns:
        if pat not in existing:
            f.write(pat + "\n")
            print(f"➕ Aggiunto a .gitignore: {pat}")

print("✅ .gitignore aggiornato")

# Commit e push
print("\n📤 Commit e push delle modifiche su GitHub...")
subprocess.run("git add .gitignore", shell=True)
subprocess.run('git commit -m "chore: update .gitignore to exclude macOS and pycache"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 60)
print("🚀 Aggiornamento .gitignore effettuato. Railway deployerà i cambiamenti automaticamente.")
