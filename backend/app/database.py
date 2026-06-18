import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to SQLite for frictionless zero-config setup, but support PostgreSQL if DATABASE_URL is supplied
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./qa_platform.db")

# SQLite requires 'check_same_thread=False' for safe use in asynchronous context
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency generator to provide transactional sessions for routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
