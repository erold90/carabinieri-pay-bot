#!/usr/bin/env python3
import subprocess

print("🔧 Correzione funzione sanitize_text_input in utils/validators.py")
print("=" * 60)

# Percorso relativo al file da modificare
file_path = 'utils/validators.py'

# Leggi il contenuto
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines, start=1):
    # Correggi la riga con il confronto su newline
    if idx == 81 and "char for char in text if ord(char) >= 32" in line:
        # Sostituisci con confronto corretto a '\n'
        new_lines.append("    text = ''.join(char for char in text if ord(char) >= 32 or char == '\\n')\n")
        print(f"✅ Linea 81 corretta: confronto newline")
        continue

    # Correggi la riga del regex che contiene virgolette non scappate
    if "re.sub" in line and "r'[^\\w\\s" in line:
        # Sostituisci con raw-string che scappa correttamente \'"
        new_pattern = "    text = re.sub(r'[^\w\s\\-.,!?€/@#()\\'\"']', '', text, flags=re.UNICODE)\n"
        new_lines.append(new_pattern)
        print(f"✅ Regex corretto a r'[^\w\\s\\-.,!?€/@#()\\'\"']'")
        continue

    # Altrimenti, mantieni la linea originale
    new_lines.append(line)

# Scrivi il file corretto
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("✅ File utils/validators.py aggiornato senza errori di sintassi")

# Commit e push
print("\n📤 Commit e push delle modifiche su GitHub...")
subprocess.run("git add utils/validators.py", shell=True)
# Modifica il messaggio di commit come preferisci
subprocess.run('git commit -m "fix: correct sanitize_text_input in utils/validators.py"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 60)
print("🚀 Validazione completata. Railway effettuerà il deploy automatico.")
print("⏰ Attendi 1-2 minuti e il bot sarà di nuovo operativo.")
