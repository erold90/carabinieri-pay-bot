from datetime import datetime, date, time, timedelta
from telegram.ext import ContextTypes
from telegram import Update
#!/usr/bin/env python3
import subprocess
import re

print("🔧 Fix formato orario in service_handler.py")
print("=" * 50)

# 1. Leggi il file
print("\n1️⃣ Analizzo service_handler.py...")
with open('handlers/service_handler.py', 'r') as f:
   content = f.read()

# 2. Aggiungi import re se mancante
if 'import re' not in content:
   import_pos = content.find('from telegram')
   if import_pos > 0:
       line_start = content.rfind('\n', 0, import_pos)
       content = content[:line_start] + '\nimport re' + content[line_start:]
       print("✅ Aggiunto import re")

# 3. Trova e sostituisci handle_time_input
print("\n2️⃣ Fix handle_time_input...")

# Nuova funzione per gestire input orario
new_time_handler = '''async def handle_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
   """Handle manual time input from user"""
   text = update.message.text.strip()
   
   # Parse time in various formats: HH:MM, HH.MM, HHMM, H:MM
   time_patterns = [
       r'^(\d{1,2}):(\d{2})$',     # HH:MM or H:MM
       r'^(\d{1,2})\.(\d{2})$',     # HH.MM or H.MM
       r'^(\d{2})(\d{2})$',         # HHMM
       r'^(\d{1,2})$'               # Just hour
   ]
   
   hour = None
   minute = 0
   
   for pattern in time_patterns:
       match = re.match(pattern, text)
       if match:
           if len(match.groups()) == 2:
               hour = int(match.group(1))
               minute = int(match.group(2))
           else:
               hour = int(match.group(1))
               minute = 0
           break
   
   if hour is not None and 0 <= hour <= 23 and 0 <= minute <= 59:
       # Valid time
       if context.user_data.get('waiting_for_start_time'):
           service_date = context.user_data['service_date']
           start_time = datetime.combine(service_date, time(hour, minute))
           context.user_data['start_time'] = start_time
           context.user_data['waiting_for_start_time'] = False
           
           text = f"⏰ Inizio: <b>{hour:02d}:{minute:02d}</b>\\n\\n"
           text += "Inserisci l'orario di fine (formato HH:MM):\\n"
           text += "Esempi: 14:30, 22:00, 2:30"
           
           await update.message.reply_text(text, parse_mode='HTML')
           context.user_data['waiting_for_end_time'] = True
           return SELECT_TIME
           
       elif context.user_data.get('waiting_for_end_time'):
           start_time = context.user_data['start_time']
           service_date = context.user_data['service_date']
           
           # Calculate end time (might be next day)
           if hour < start_time.hour or (hour == start_time.hour and minute <= start_time.minute):
               # Next day
               end_date = service_date + timedelta(days=1)
           else:
               end_date = service_date
           
           end_time = datetime.combine(end_date, time(hour, minute))
           context.user_data['end_time'] = end_time
           context.user_data['waiting_for_end_time'] = False
           
           # Calculate total hours
           total_hours = (end_time - start_time).total_seconds() / 3600
           context.user_data['total_hours'] = total_hours
           
           # Check for double shift
           is_double = total_hours > 12
           context.user_data['is_double_shift'] = is_double
           
           text = f"⏰ <b>ORARIO COMPLETO</b>\\n\\n"
           text += f"Dalle: {start_time.strftime('%H:%M')} "
           text += f"Alle: {end_time.strftime('%H:%M')}\\n\\n"
           text += f"✅ Totale: <b>{total_hours:.0f} ore</b>\\n"
           
           if is_double:
               text += "\\n⚠️ <b>DOPPIA TURNAZIONE RILEVATA!</b>\\n\\n"
               text += f"Servizio di {total_hours:.0f} ore = 2 turni esterni\\n\\n"
               text += "✅ Applicati automaticamente:\\n"
               text += "├ 1° turno esterno: €5,45\\n"
               text += "├ 2° turno esterno: €5,45\\n"
               text += "└ Totale: €10,90\\n"
           
           # Check if escort was pre-selected
           if context.user_data.get('preselected_escort'):
               context.user_data['service_type'] = ServiceType.ESCORT
               return await ask_escort_details(update, context)
           
           text += "\\n\\nTipo di servizio?"
           
           await update.message.reply_text(
               text,
               parse_mode='HTML',
               reply_markup=get_service_type_keyboard()
           )
           
           return SELECT_SERVICE_TYPE
           
   else:
       await update.message.reply_text(
           "❌ Orario non valido! Usa il formato HH:MM\\n"
           "Esempi validi: 08:30, 14:45, 22:00, 8:30",
           parse_mode='HTML'
       )
       return SELECT_TIME'''

# Trova e sostituisci handle_time_input
if 'async def handle_time_input' in content:
   # Trova inizio e fine della funzione
   start = content.find('async def handle_time_input')
   # Trova la prossima async def o def
   next_def = content.find('\nasync def', start + 1)
   if next_def == -1:
       next_def = content.find('\ndef', start + 1)
   
   if next_def != -1:
       content = content[:start] + new_time_handler + '\n\n' + content[next_def:]
   else:
       content = content[:start] + new_time_handler
else:
   # Aggiungi prima del conversation handler
   conv_pos = content.find('service_conversation_handler = ConversationHandler')
   if conv_pos > 0:
       content = content[:conv_pos] + new_time_handler + '\n\n' + content[conv_pos:]

print("✅ Funzione handle_time_input aggiornata")

# 4. Salva il file
with open('handlers/service_handler.py', 'w') as f:
   f.write(content)

print("✅ File salvato")

# 5. Git commit e push
print("\n3️⃣ Commit e push...")
subprocess.run("git add handlers/service_handler.py", shell=True)
subprocess.run('git commit -m "fix: migliorato parsing formato orario - accetta HH:MM, H:MM, HH.MM"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Fix completato!")
print("\n⏰ Railway farà il deploy automaticamente in 2-3 minuti")
print("\n📱 Formati orario ora accettati:")
print("  - 08:30 (standard)")
print("  - 8:30 (senza zero)")
print("  - 08.30 (con punto)")
print("  - 0830 (senza separatore)")
print("  - 8 (solo ora)")
