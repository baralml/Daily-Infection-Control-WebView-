from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Create engine for synchronous operations (psycopg2)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # checks connection health on checkout
    pool_size=10,
    max_overflow=20
)

# SessionLocal is the session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

def get_db():
    """Dependency generator for database sessions.
    Guarantees session cleanup after request cycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
