"""
Servizio per la gestione degli straordinari
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from database.models import User, Overtime, OvertimeType
from config.constants import OVERTIME_RATES

class OvertimeService:
    """Gestisce tutta la logica relativa agli straordinari"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_monthly_overtime(self, user_id: int, month: int, year: int):
        """Ottieni straordinari del mese con totali"""
        overtimes = self.db.query(Overtime).filter(
            Overtime.user_id == user_id,
            extract('month', Overtime.date) == month,
            extract('year', Overtime.date) == year
        ).all()
        
        # Calcola totali
        by_type = {}
        paid_hours = 0
        paid_amount = 0
        unpaid_hours = 0
        unpaid_amount = 0
        
        for ot in overtimes:
            type_key = ot.overtime_type.value
            if type_key not in by_type:
                by_type[type_key] = {'hours': 0, 'amount': 0}
            
            by_type[type_key]['hours'] += ot.hours
            by_type[type_key]['amount'] += ot.amount
            
            if ot.is_paid:
                paid_hours += ot.hours
                paid_amount += ot.amount
            else:
                unpaid_hours += ot.hours
                unpaid_amount += ot.amount
        
        return {
            'by_type': by_type,
            'paid': {'hours': paid_hours, 'amount': paid_amount},
            'unpaid': {'hours': unpaid_hours, 'amount': unpaid_amount},
            'total': {'hours': paid_hours + unpaid_hours, 'amount': paid_amount + unpaid_amount}
        }
    
    def get_accumulated_overtime(self, user_id: int):
        """Ottieni totale straordinari non pagati"""
        result = self.db.query(
            func.sum(Overtime.hours),
            func.sum(Overtime.amount)
        ).filter(
            Overtime.user_id == user_id,
            Overtime.is_paid == False
        ).first()
        
        return {
            'hours': result[0] or 0,
            'amount': result[1] or 0
        }
    
    def mark_hours_as_paid(self, user_id: int, hours_to_pay: float, payment_date: datetime.date):
        """Marca ore come pagate con gestione transazionale"""
        try:
            # Ottieni straordinari non pagati in ordine cronologico
            unpaid = self.db.query(Overtime).filter(
                Overtime.user_id == user_id,
                Overtime.is_paid == False
            ).order_by(Overtime.date).all()
            
            remaining_hours = hours_to_pay
            paid_amount = 0
            
            for ot in unpaid:
                if remaining_hours <= 0:
                    break
                
                if ot.hours <= remaining_hours:
                    # Paga completamente
                    ot.is_paid = True
                    ot.paid_date = payment_date
                    ot.payment_month = f"{payment_date.year}-{payment_date.month:02d}"
                    remaining_hours -= ot.hours
                    paid_amount += ot.amount
                else:
                    # Pagamento parziale - crea nuovo record per la parte non pagata
                    unpaid_hours = ot.hours - remaining_hours
                    unpaid_ratio = unpaid_hours / ot.hours
                    unpaid_amount = ot.amount * unpaid_ratio
                    
                    # Aggiorna record originale
                    ot.hours = remaining_hours
                    ot.amount = ot.amount * (remaining_hours / (remaining_hours + unpaid_hours))
                    ot.is_paid = True
                    ot.paid_date = payment_date
                    ot.payment_month = f"{payment_date.year}-{payment_date.month:02d}"
                    
                    # Crea nuovo record per parte non pagata
                    new_ot = Overtime(
                        user_id=ot.user_id,
                        service_id=ot.service_id,
                        date=ot.date,
                        hours=unpaid_hours,
                        overtime_type=ot.overtime_type,
                        hourly_rate=ot.hourly_rate,
                        amount=unpaid_amount,
                        is_paid=False
                    )
                    self.db.add(new_ot)
                    
                    paid_amount += ot.amount
                    remaining_hours = 0
            
            self.db.commit()
            return {'success': True, 'paid_hours': hours_to_pay, 'paid_amount': paid_amount}
            
        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': str(e)}
