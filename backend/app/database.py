import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Get the absolute directory of the backend folder (C:\QAAgents\backend)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
default_db_path = os.path.join(backend_dir, "qa_platform.db").replace("\\", "/")

# Force absolute file path for SQLite to prevent working directory shifts!
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{default_db_path}")

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
