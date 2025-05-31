"""
Database connection and session management - VERSIONE ROBUSTA
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from contextlib import contextmanager

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

logger.info(f"Database URL: {DATABASE_URL[:30]}...")

# Create engine con retry e gestione errori
engine = None
SessionLocal = None

def create_db_engine():
    """Crea engine con gestione errori e retry"""
    global engine, SessionLocal
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if DATABASE_URL.startswith("postgresql"):
                engine = create_engine(
                    DATABASE_URL,
                    poolclass=NullPool,
                    echo=False,
                    connect_args={
                        "connect_timeout": 10,
                        "options": "-c statement_timeout=30000"
                    }
                )
            else:
                engine = create_engine(DATABASE_URL, echo=False)
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            logger.info("✅ Database engine creato con successo")
            return True
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Tentativo {retry_count}/{max_retries} fallito: {e}")
            if retry_count >= max_retries:
                logger.error("Impossibile connettersi al database dopo 3 tentativi")
                # Fallback a SQLite
                try:
                    engine = create_engine("sqlite:///fallback.db", echo=False)
                    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                    logger.warning("Fallback a SQLite locale")
                    return True
                except:
                    return False
    
    return False

# Inizializza engine
create_db_engine()

# Create base class for models
Base = declarative_base()

@contextmanager
def get_db():
    """Context manager per sessioni database"""
    if not SessionLocal:
        if not create_db_engine():
            raise Exception("Database non disponibile")
    
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    if not engine:
        if not create_db_engine():
            return False
    
    try:
        from .models import User, Service, Overtime, TravelSheet, Leave, Rest
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        return False

def test_connection():
    """Test database connection"""
    if not engine:
        if not create_db_engine():
            return False
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection OK")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
