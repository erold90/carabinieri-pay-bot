"""
Sistema di notifiche automatiche
"""
import asyncio
from datetime import datetime, timedelta, date
from telegram import Bot
from sqlalchemy import extract, and_

from database.connection import SessionLocal
from database.models import User, Leave, Overtime, TravelSheet
from config.settings import TIMEZONE
from utils.formatters import format_currency, format_date

class NotificationSystem:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.running = False
        
    async def start(self):
        """Avvia il sistema di notifiche"""
        self.running = True
        while self.running:
            try:
                await self.check_and_send_notifications()
                # Controlla ogni ora
                await asyncio.sleep(3600)
            except Exception as e:
                print(f"Errore notifiche: {e}")
                await asyncio.sleep(300)  # Riprova dopo 5 minuti
    
    async def check_and_send_notifications(self):
        """Controlla e invia notifiche"""
        current_time = datetime.now(TIMEZONE)
        current_hour = current_time.hour
        
        db = SessionLocal()
        try:
            # Prendi tutti gli utenti con notifiche attive
            users = db.query(User).filter(
                User.notification_settings != None
            ).all()
            
            for user in users:
                notifications = user.notification_settings or {}
                reminder_hour = int(notifications.get('reminder_time', '09:00').split(':')[0])
                
                # Invia solo all'ora configurata
                if current_hour != reminder_hour:
                    continue
                
                # Daily reminder
                if notifications.get('daily_reminder'):
                    await self.send_daily_reminder(user, db)
                
                # Overtime limit
                if notifications.get('overtime_limit'):
                    await self.check_overtime_limit(user, db)
                
                # Leave expiry
                if notifications.get('leave_expiry'):
                    await self.check_leave_expiry(user, db)
                
                # Travel sheet reminder
                if notifications.get('travel_sheet_reminder'):
                    await self.check_travel_sheets(user, db)
                    
        finally:
            db.close()
    
    async def send_daily_reminder(self, user: User, db):
        """Invia promemoria giornaliero"""
        try:
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            # Controlla se ha registrato il servizio di ieri
            from database.models import Service
            yesterday_service = db.query(Service).filter(
                Service.user_id == user.id,
                Service.date == yesterday
            ).first()
            
            if not yesterday_service:
                text = "🔔 <b>PROMEMORIA GIORNALIERO</b>\n\n"
                text += f"Non hai ancora registrato il servizio di ieri {format_date(yesterday)}!\n\n"
                text += "Usa /nuovo per registrarlo ora."
                
                await self.bot.send_message(
                    chat_id=user.chat_id,
                    text=text,
                    parse_mode='HTML'
                )
        except:
            pass
    
    async def check_overtime_limit(self, user: User, db):
        """Controlla limite straordinari mensili"""
        try:
            current_month = date.today().month
            current_year = date.today().year
            
            # Calcola ore pagate questo mese
            paid_hours = db.query(func.sum(Overtime.hours)).filter(
                Overtime.user_id == user.id,
                extract('month', Overtime.date) == current_month,
                extract('year', Overtime.date) == current_year,
                Overtime.is_paid == True
            ).scalar() or 0
            
            if paid_hours >= 50:  # Alert a 50 ore
                text = "⚠️ <b>LIMITE STRAORDINARI</b>\n\n"
                text += f"Hai già {paid_hours:.0f} ore pagate questo mese!\n"
                text += "Limite massimo: 55 ore\n\n"
                text += "Le prossime ore saranno accumulate."
                
                await self.bot.send_message(
                    chat_id=user.chat_id,
                    text=text,
                    parse_mode='HTML'
                )
        except:
            pass
    
    async def check_leave_expiry(self, user: User, db):
        """Controlla scadenza licenze"""
        try:
            if user.previous_year_leave > 0:
                current_year = date.today().year
                deadline = date(current_year, 3, 31)
                days_left = (deadline - date.today()).days
                
                if 0 < days_left <= 30:  # Alert ultimo mese
                    text = "🏖️ <b>LICENZE IN SCADENZA!</b>\n\n"
                    text += f"Hai {user.previous_year_leave} giorni di licenza {current_year-1} "
                    text += f"che scadono tra {days_left} giorni!\n\n"
                    text += "Pianifica subito con /licenze"
                    
                    await self.bot.send_message(
                        chat_id=user.chat_id,
                        text=text,
                        parse_mode='HTML'
                    )
        except:
            pass
    
    async def check_travel_sheets(self, user: User, db):
        """Controlla fogli viaggio non pagati"""
        try:
            # FV più vecchio di 90 giorni
            old_sheets = db.query(TravelSheet).filter(
                TravelSheet.user_id == user.id,
                TravelSheet.is_paid == False,
                TravelSheet.date < date.today() - timedelta(days=90)
            ).all()
            
            if old_sheets:
                total_amount = sum(s.amount for s in old_sheets)
                oldest = min(old_sheets, key=lambda x: x.date)
                days = (date.today() - oldest.date).days
                
                text = "📋 <b>FOGLI VIAGGIO DA SOLLECITARE</b>\n\n"
                text += f"Hai {len(old_sheets)} FV non pagati da oltre 90 giorni!\n"
                text += f"Importo totale: {format_currency(total_amount)}\n"
                text += f"FV più vecchio: {days} giorni\n\n"
                text += "Verifica con /fv"
                
                await self.bot.send_message(
                    chat_id=user.chat_id,
                    text=text,
                    parse_mode='HTML'
                )
        except:
            pass

# Istanza globale
notification_system = None

def start_notification_system(bot: Bot):
    """Avvia il sistema di notifiche"""
    global notification_system
    notification_system = NotificationSystem(bot)
    asyncio.create_task(notification_system.start())
