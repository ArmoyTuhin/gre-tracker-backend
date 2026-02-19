from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get database URL from environment variable (for Railway) or use default
# For local development, use SQLite if PostgreSQL is not available
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Try SQLite for local development (no setup required)
    # Use absolute path to ensure database persists regardless of working directory
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(backend_dir, "gre_tracker.db")
    DATABASE_URL = f"sqlite:///{db_path}"
    print("⚠ Using SQLite for local development. For PostgreSQL, set DATABASE_URL environment variable.")
    print(f"📁 Database location: {db_path}")
else:
    # Remove 'postgres://' and replace with 'postgresql://' for SQLAlchemy compatibility
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite needs check_same_thread=False, PostgreSQL doesn't
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

