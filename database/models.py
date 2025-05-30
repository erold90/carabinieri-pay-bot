"""
Database models for CarabinieriPayBot
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .connection import Base
from config.settings import get_current_datetime

class ServiceType(str, enum.Enum):
    LOCAL = "LOCAL"
    ESCORT = "ESCORT"
    MISSION = "MISSION"

class OvertimeType(str, enum.Enum):
    WEEKDAY_DAY = "WEEKDAY_DAY"
    WEEKDAY_NIGHT = "WEEKDAY_NIGHT"
    HOLIDAY_DAY = "HOLIDAY_DAY"
    HOLIDAY_NIGHT = "HOLIDAY_NIGHT"

class LeaveType(str, enum.Enum):
    ORDINARY_CURRENT = "ORDINARY_CURRENT"
    ORDINARY_PREVIOUS = "ORDINARY_PREVIOUS"
    SICK = "SICK"
    BLOOD_DONATION = "BLOOD_DONATION"
    LAW_104 = "LAW_104"
    STUDY = "STUDY"
    MARRIAGE = "MARRIAGE"
    OTHER = "OTHER"


class RestType(str, enum.Enum):
    WEEKLY = "WEEKLY"  # Riposo settimanale
    HOLIDAY = "HOLIDAY"  # Festività infrasettimanale
    COMPENSATORY = "COMPENSATORY"  # Riposo compensativo per straordinari

class Rest(Base):
    __tablename__ = "rests"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Dettagli riposo
    rest_type = Column(Enum(RestType), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    actual_date = Column(Date)  # Se diversa dalla pianificata
    
    # Stato
    is_completed = Column(Boolean, default=False)
    is_worked = Column(Boolean, default=False)  # Se ha lavorato invece di riposare
    work_reason = Column(String)  # Motivo del richiamo
    
    # Recupero
    recovery_due_date = Column(Date)  # Entro 4 settimane
    recovery_date = Column(Date)  # Quando effettivamente recuperato
    is_recovered = Column(Boolean, default=False)
    
    # Riferimenti
    service_id = Column(Integer, ForeignKey("services.id"))  # Servizio che ha sostituito il riposo
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_datetime)
    updated_at = Column(DateTime, default=get_current_datetime, onupdate=get_current_datetime)
    
    # Relationships
    user = relationship("User", back_populates="rests")
    rest_replaced = relationship("Rest", back_populates="service", uselist=False)
    service = relationship("Service", back_populates="rest_replaced")

# Aggiungi relazione in Service
# rest_replaced = relationship("Rest", back_populates="service", uselist=False)

# Aggiungi in User
# rests = relationship("Rest", back_populates="user", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False, index=True)
    chat_id = Column(String, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    
    # Personal data
    rank = Column(String)
    parameter = Column(Float, default=108.5)
    irpef_rate = Column(Float, default=0.27)
    base_shift_hours = Column(Integer, default=6)
    years_of_service = Column(Integer, default=0)
    command = Column(String)
    
    # Leave management
    current_year_leave = Column(Integer, default=32)
    current_year_leave_used = Column(Integer, default=0)
    previous_year_leave = Column(Integer, default=0)
    
    # Settings
    patron_saint_date = Column(Date)
    saved_routes = Column(JSON, default=dict)
    notification_settings = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_datetime)
    updated_at = Column(DateTime, default=get_current_datetime, onupdate=get_current_datetime)
    
    # Relationships
    services = relationship("Service", back_populates="user", cascade="all, delete-orphan")
    overtimes = relationship("Overtime", back_populates="user", cascade="all, delete-orphan")
    travel_sheets = relationship("TravelSheet", back_populates="user", cascade="all, delete-orphan")
    leaves = relationship("Leave", back_populates="user", cascade="all, delete-orphan")
    rests = relationship("Rest", back_populates="user", cascade="all, delete-orphan")

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Service details
    date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_hours = Column(Float, nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    
    # Status
    is_holiday = Column(Boolean, default=False)
    is_super_holiday = Column(Boolean, default=False)
    is_double_shift = Column(Boolean, default=False)
    called_from_leave = Column(Boolean, default=False)
    called_from_rest = Column(Boolean, default=False)
    recovery_hours = Column(Float, default=0)
    
    # Escort specific
    travel_sheet_number = Column(String)
    destination = Column(String)
    km_total = Column(Integer, default=0)
    active_travel_hours = Column(Float, default=0)
    passive_travel_hours = Column(Float, default=0)
    
    # Mission details
    mission_type = Column(String)  # ORDINARY or FORFEIT
    forfeit_amount = Column(Float, default=0)
    meals_consumed = Column(Integer, default=0)
    meal_reimbursement = Column(Float, default=0)
    
    # Calculations
    overtime_amount = Column(Float, default=0)
    allowances_amount = Column(Float, default=0)
    mission_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)
    
    # JSON for detailed breakdown
    calculation_details = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_datetime)
    updated_at = Column(DateTime, default=get_current_datetime, onupdate=get_current_datetime)
    
    # Relationships
    user = relationship("User", back_populates="services")

class Overtime(Base):
    __tablename__ = "overtimes"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"))
    
    # Overtime details
    date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    overtime_type = Column(Enum(OvertimeType), nullable=False)
    hourly_rate = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    
    # Payment status
    is_paid = Column(Boolean, default=False)
    paid_date = Column(Date)
    payment_month = Column(String)  # Format: "2024-12"
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_datetime)
    
    # Relationships
    user = relationship("User", back_populates="overtimes")

class TravelSheet(Base):
    __tablename__ = "travel_sheets"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"))
    
    # Travel sheet details
    sheet_number = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    destination = Column(String)
    amount = Column(Float, nullable=False)
    
    # Payment status
    is_paid = Column(Boolean, default=False)
    paid_date = Column(Date)
    payment_reference = Column(String)
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_datetime)
    updated_at = Column(DateTime, default=get_current_datetime, onupdate=get_current_datetime)
    
    # Relationships
    user = relationship("User", back_populates="travel_sheets")

class Leave(Base):
    __tablename__ = "leaves"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Leave details
    leave_type = Column(Enum(LeaveType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days = Column(Integer, nullable=False)
    notes = Column(String)
    
    # Status
    is_approved = Column(Boolean, default=True)
    is_cancelled = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=get_current_datetime)
    updated_at = Column(DateTime, default=get_current_datetime, onupdate=get_current_datetime)
    
    # Relationships
    user = relationship("User", back_populates="leaves")