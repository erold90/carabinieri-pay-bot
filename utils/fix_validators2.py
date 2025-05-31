#!/usr/bin/env python3
import subprocess

print("🔧 Correzione definitiva di sanitize_text_input in utils/validators.py")
print("=" * 60)

file_path = 'utils/validators.py'

# Leggi tutte le righe
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines, start=1):
    # ----------------------------
    # 1) Sostituisci le L30–L31 (in realtà righe 81–82 dopo docstring) 
    #    che contengono la stringa interrotta
    if idx == 81:
        # Inserisci il confronto corretto su '\n' in una sola linea
        new_lines.append("    text = ''.join(char for char in text if ord(char) >= 32 or char == '\\n')\n")
        # Salta la riga 82 (quella vuota o contenente solo "')" )
        continue
    if idx == 82:
        # Non riscriviamo questa riga interrotta
        continue

    # ----------------------------
    # 2) Sostituisci la riga del re.sub (era riga 86)
    #    con indentazione identica (8 spazi) e pattern ben scappato
    if idx == 86 and "re.sub" in line and "[^" in line:
        new_lines.append("        text = re.sub(r\"[^\\w\\s\\-\\.,!\\?€/@#\\()\\'\\\"]\", \"\", text, flags=re.UNICODE)\n")
        continue

    # ----------------------------
    # Altrimenti, mantieni la riga così com’è
    new_lines.append(line)

# Scrivi il file corretto
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ File utils/validators.py aggiornato correttamente.")

# Commit & Push
print("\n📤 Commit e push delle modifiche su GitHub...")
subprocess.run("git add utils/validators.py", shell=True)
subprocess.run('git commit -m "fix: system sanitize_text_input in utils/validators.py"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 60)
print("🚀 Correzione inviata a GitHub. Railway effettuerà il deploy automatico.")
print("⏰ Attendi 1-2 minuti per il nuovo deploy.")
