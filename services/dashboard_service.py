"""
Servizio per aggregare dati del dashboard
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import extract, func

from database.models import User, Service, Overtime, TravelSheet, Leave
from services.calculation_service import calculate_month_totals

class DashboardService:
    """Servizio ottimizzato per il dashboard"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_data(self, user_id: int, current_date: datetime.date):
        """Ottieni tutti i dati del dashboard con query ottimizzate"""
        # Una singola query per i dati del mese
        month_data = calculate_month_totals(
            self.db, user_id, current_date.month, current_date.year
        )
        
        # Query aggregate per straordinari e fogli viaggio
        overtime_stats = self.db.query(
            func.sum(Overtime.hours).filter(Overtime.is_paid == False),
            func.sum(Overtime.amount).filter(Overtime.is_paid == False)
        ).filter(Overtime.user_id == user_id).first()
        
        travel_stats = self.db.query(
            func.count(TravelSheet.id).filter(TravelSheet.is_paid == False),
            func.sum(TravelSheet.amount).filter(TravelSheet.is_paid == False),
            func.min(TravelSheet.date).filter(TravelSheet.is_paid == False)
        ).filter(TravelSheet.user_id == user_id).first()
        
        return {
            'month_data': month_data,
            'unpaid_overtime': {
                'hours': overtime_stats[0] or 0,
                'amount': overtime_stats[1] or 0
            },
            'unpaid_travel_sheets': {
                'count': travel_stats[0] or 0,
                'amount': travel_stats[1] or 0,
                'oldest_date': travel_stats[2]
            }
        }
