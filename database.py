"""
database.py - Database configuration and session management.

Uses SQLAlchemy with SQLite. The database file is stored in the ./data/ directory
and is created automatically on first run.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# ---------------------------------------------------------------------------
# Base class for all models
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class that all SQLAlchemy models inherit from."""
    pass


# ---------------------------------------------------------------------------
# Database path & engine setup
# ---------------------------------------------------------------------------
# Store the database inside the data/ folder (created automatically).
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Read DATABASE_URL from env or Streamlit secrets, defaulting to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
            DATABASE_URL = str(st.secrets["DATABASE_URL"])
    except Exception:
        pass

if not DATABASE_URL:
    DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'smart_education.db')}"
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)

# Session factory — use this to get a new session wherever needed.
SessionLocal = sessionmaker(bind=engine)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def init_db():
    """Create all tables that don't exist yet.

    Call this once at application startup. It is safe to call multiple times —
    existing tables are left untouched.
    """
    # Import models so SQLAlchemy knows about them before creating tables.
    import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_session():
    """Return a new database session.

    Usage:
        session = get_session()
        try:
            # ... work with session ...
            session.commit()
        finally:
            session.close()
    """
    return SessionLocal()
