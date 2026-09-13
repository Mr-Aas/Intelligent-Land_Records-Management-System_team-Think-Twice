"""
SQLAlchemy Engine & Database Session Management for PostgreSQL + PostGIS (§12).
"""

from __future__ import annotations

import logging
from typing import Generator, Optional, Tuple

from app.pipeline import config
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger(__name__)

# Base class for SQLAlchemy ORM models
Base = declarative_base()

# SQLAlchemy engine initialization with connection pool settings
_engine = None
_SessionLocal = None


def get_engine():
    """Lazily initialize and return the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        db_url = config.DATABASE_URL
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args={"connect_timeout": 5},
        )
    return _engine


def get_session_factory():
    """Lazily initialize and return the sessionmaker."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _SessionLocal


def get_db() -> Generator:
    """FastAPI dependency yielding a database session."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection(db_url: Optional[str] = None) -> Tuple[bool, str]:
    """
    Test direct connection to PostgreSQL database.

    Returns:
        (is_connected: bool, details_message: str)
    """
    target_url = db_url or config.DATABASE_URL
    try:
        conn = psycopg2.connect(target_url, connect_timeout=3)
        cursor = conn.cursor()
        cursor.execute("SELECT 1;")
        cursor.fetchone()
        conn.close()
        return True, "Successfully connected to PostgreSQL database."
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def get_postgis_version(db_url: Optional[str] = None) -> Optional[str]:
    """Check PostGIS extension version if available in PostgreSQL database."""
    target_url = db_url or config.DATABASE_URL
    try:
        conn = psycopg2.connect(target_url, connect_timeout=3)
        cursor = conn.cursor()
        cursor.execute("SELECT PostGIS_Version();")
        res = cursor.fetchone()
        conn.close()
        return res[0] if res else None
    except Exception:
        return None
