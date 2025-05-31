"""
Database connection and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
import logging

logger = logging.getLogger(__name__)

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')

# Handle Railway PostgreSQL URL format
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Fallback per sviluppo locale
if not DATABASE_URL:
    logger.warning("DATABASE_URL non trovato, uso SQLite locale")
    DATABASE_URL = "sqlite:///local_carabinieri.db"

logger.info(f"Database URL: {DATABASE_URL[:20]}...")

# Create engine con gestione errori
try:
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,  # Disable connection pooling for Railway
        echo=False,
        # Aggiungi timeout per evitare hang
        connect_args={
            "connect_timeout": 10
        } if DATABASE_URL.startswith("postgresql") else {}
    )
except Exception as e:
    logger.error(f"Errore creazione engine: {e}")
    # Fallback a SQLite
    logger.warning("Fallback a SQLite locale")
    engine = create_engine("sqlite:///fallback.db", echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from .models import User, Service, Overtime, TravelSheet, Leave, Rest
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        # Non sollevare eccezione, il bot può funzionare anche senza DB
        return False

def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✅ Database connection OK")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
