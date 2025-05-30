from datetime import datetime, date, time, timedelta
from telegram.ext import ContextTypes
from telegram import Update
#!/usr/bin/env python3
import subprocess

print("🕐 Miglioramento inserimento orari")
print("=" * 50)

# 1. Modifica service_handler.py per input orario manuale
service_handler_fix = '''
# Trova la funzione handle_start_time e sostituiscila
async def handle_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle start time selection or input"""
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_time_manual":
            # L'utente vuole inserire manualmente
            text = "⏰ <b>ORARIO DI INIZIO</b>\\n\\n"
            text += "Inserisci l'orario di inizio nel formato HH:MM\\n"
            text += "Esempi: 06:30, 14:45, 22:00"
            
            await query.edit_message_text(text, parse_mode='HTML')
            context.user_data['waiting_for_start_time'] = True
            return SELECT_TIME
    
    elif update.message:
        # Input manuale dell'orario
        try:
            time_parts = update.message.text.strip().split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                service_date = context.user_data['service_date']
                start_time = datetime.combine(service_date, time(hour, minute))
                context.user_data['start_time'] = start_time
                context.user_data['waiting_for_start_time'] = False
                
                text = f"⏰ Inizio: <b>{hour:02d}:{minute:02d}</b>\\n\\n"
                text += "Ora inserisci l'orario di fine nel formato HH:MM\\n"
                text += "Esempi: 12:30, 18:45, 02:00 (del giorno dopo)"
                
                await update.message.reply_text(text, parse_mode='HTML')
                context.user_data['waiting_for_end_time'] = True
                return SELECT_SERVICE_TYPE
            else:
                await update.message.reply_text(
                    "❌ Orario non valido! Usa il formato HH:MM (es: 06:30)",
                    parse_mode='HTML'
                )
                return SELECT_TIME
                
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ Formato non valido! Usa HH:MM (es: 06:30)",
                parse_mode='HTML'
            )
            return SELECT_TIME

async def handle_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle end time input"""
    if update.message and context.user_data.get('waiting_for_end_time'):
        try:
            time_parts = update.message.text.strip().split(':')
            hour = int(time_parts[0])
            minute = int(time_parts[1]) if len(time_parts) > 1 else 0
            
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                start_time = context.user_data['start_time']
                
                # Determina se l'orario di fine è nel giorno dopo
                if hour < start_time.hour or (hour == start_time.hour and minute < start_time.minute):
                    # Orario di fine è nel giorno dopo
                    end_date = start_time.date() + timedelta(days=1)
                else:
                    end_date = start_time.date()
                
                end_time = datetime.combine(end_date, time(hour, minute))
                context.user_data['end_time'] = end_time
                context.user_data['waiting_for_end_time'] = False
                
                # Calcola ore totali
                total_hours = (end_time - start_time).total_seconds() / 3600
                context.user_data['total_hours'] = total_hours
                
                # Check per doppio turno
                is_double = total_hours > 12
                context.user_data['is_double_shift'] = is_double
                
                text = f"⏰ <b>ORARIO COMPLETO</b>\\n\\n"
                text += f"Dalle: {start_time.strftime('%H:%M')} "
                text += f"Alle: {end_time.strftime('%H:%M')}"
                if end_date != start_time.date():
                    text += " (giorno dopo)"
                text += f"\\n\\n✅ Totale: <b>{total_hours:.1f} ore</b>\\n"
                
                if is_double:
                    text += "\\n⚠️ <b>DOPPIA TURNAZIONE RILEVATA!</b>\\n\\n"
                    text += f"Servizio di {total_hours:.1f} ore = 2 turni esterni\\n\\n"
                    text += "✅ Applicati automaticamente:\\n"
                    text += "├ 1° turno esterno: €5,45\\n"
                    text += "├ 2° turno esterno: €5,45\\n"
                    text += "└ Totale: €10,90\\n"
                
                text += "\\n\\nTipo di servizio?"
                
                await update.message.reply_text(
                    text,
                    parse_mode='HTML',
                    reply_markup=get_service_type_keyboard()
                )
                
                return SELECT_SERVICE_TYPE
            else:
                await update.message.reply_text(
                    "❌ Orario non valido! Usa il formato HH:MM",
                    parse_mode='HTML'
                )
                return SELECT_SERVICE_TYPE
                
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ Formato non valido! Usa HH:MM (es: 18:30)",
                parse_mode='HTML'
            )
            return SELECT_SERVICE_TYPE
'''

# Leggi il file service_handler.py
with open('handlers/service_handler.py', 'r') as f:
    content = f.read()

# Trova e modifica la funzione handle_status_selection per usare input manuale
new_status_function = '''async def handle_status_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle personal status selection"""
    query = update.callback_query
    await query.answer()
    
    status = query.data.replace("status_", "")
    context.user_data['personal_status'] = status
    
    if status in ['leave', 'rest']:
        context.user_data['called_from_leave'] = (status == 'leave')
        context.user_data['called_from_rest'] = (status == 'rest')
        
        text = "⚠️ <b>RICHIAMO IN SERVIZIO!</b>\\n"
        text += "✅ Compensazione €10,90 applicata\\n"
        if status == 'leave':
            text += "✅ Licenza scalata automaticamente\\n"
    else:
        text = ""
    
    text += "\\n⏰ <b>ORARIO SERVIZIO</b>\\n\\n"
    text += "Inserisci l'orario di inizio (formato HH:MM):\\n"
    text += "Esempi: 06:30, 14:45, 22:00"
    
    await query.edit_message_text(text, parse_mode='HTML')
    context.user_data['waiting_for_start_time'] = True
    
    return SELECT_TIME'''

# Trova la posizione della funzione handle_status_selection
status_pos = content.find('async def handle_status_selection')
if status_pos != -1:
    # Trova la fine della funzione
    next_async = content.find('async def', status_pos + 1)
    if next_async != -1:
        # Sostituisci la funzione
        content = content[:status_pos] + new_status_function + '\n\n' + content[next_async:]

# Aggiungi le nuove funzioni per gestire l'input manuale se non esistono
if 'waiting_for_start_time' not in content:
    # Aggiungi dopo handle_status_selection
    content = content.replace(
        'return SELECT_TIME',
        '''return SELECT_TIME

async def handle_time_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle manual time input"""
    if context.user_data.get('waiting_for_start_time'):
        return await handle_start_time(update, context)
    elif context.user_data.get('waiting_for_end_time'):
        return await handle_end_time(update, context)
    
    return SELECT_TIME'''
    )

# Modifica il conversation handler per gestire input di testo
conversation_handler_fix = '''
        SELECT_TIME: [
            CallbackQueryHandler(handle_status_selection, pattern="^status_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_input)
        ],
        SELECT_SERVICE_TYPE: [
            CallbackQueryHandler(handle_service_type, pattern="^service_type_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_input)
        ],'''

# Trova e sostituisci la sezione states nel ConversationHandler
states_pos = content.find('states={')
if states_pos != -1:
    # Trova SELECT_TIME e SELECT_SERVICE_TYPE
    select_time_pos = content.find('SELECT_TIME:', states_pos)
    if select_time_pos != -1:
        # Trova la fine di SELECT_SERVICE_TYPE
        bracket_count = 0
        i = select_time_pos
        start_pos = None
        while i < len(content):
            if content[i] == '[':
                if start_pos is None:
                    start_pos = i
                bracket_count += 1
            elif content[i] == ']':
                bracket_count -= 1
                if bracket_count == 0 and content[i-1] != '\\':
                    # Trovata la fine, cerca SELECT_SERVICE_TYPE
                    next_section = content.find('SELECT_SERVICE_TYPE:', i)
                    if next_section != -1:
                        # Trova la fine di questa sezione
                        j = next_section
                        bracket_count2 = 0
                        start_pos2 = None
                        while j < len(content):
                            if content[j] == '[':
                                if start_pos2 is None:
                                    start_pos2 = j
                                bracket_count2 += 1
                            elif content[j] == ']':
                                bracket_count2 -= 1
                                if bracket_count2 == 0:
                                    # Sostituisci entrambe le sezioni
                                    content = content[:select_time_pos] + conversation_handler_fix + content[j+2:]
                                    break
                            j += 1
                    break
            i += 1

# Aggiungi le funzioni complete per handle_start_time e handle_end_time
if 'async def handle_start_time' not in content:
    # Trova un buon posto per inserirle (dopo handle_status_selection)
    insert_pos = content.find('return SELECT_TIME')
    if insert_pos != -1:
        insert_pos = content.find('\n\n', insert_pos) + 2
        content = content[:insert_pos] + service_handler_fix + '\n\n' + content[insert_pos:]

# Salva il file modificato
with open('handlers/service_handler.py', 'w') as f:
    f.write(content)

print("✅ Modificato service_handler.py per input orario manuale")

# Commit e push
print("\n📤 Commit e push...")
subprocess.run("git add handlers/service_handler.py", shell=True)
subprocess.run('git commit -m "feat: input manuale orari con formato HH:MM per maggiore flessibilità"', shell=True)
subprocess.run("git push origin main", shell=True)

print("\n" + "=" * 50)
print("✅ Miglioramento completato!")
print("\n🕐 Ora puoi inserire orari precisi come:")
print("   - 06:30")
print("   - 14:45") 
print("   - 22:15")
print("\n📱 Il bot gestisce automaticamente:")
print("   - Turni che finiscono il giorno dopo")
print("   - Calcolo ore totali con minuti")
print("   - Rilevamento doppi turni")
