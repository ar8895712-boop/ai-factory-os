# ==============================================================
# backend/database.py — SQLAlchemy engine, session & base
# ==============================================================
"""
Database connection layer.  Uses SQLite for development,
PostgreSQL-ready via a single URL swap in config.yaml.

Usage:
    from backend.database import get_db, engine, Base
    # In FastAPI endpoints, use `Depends(get_db)`.
"""

from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import get_settings

import os
from pathlib import Path

# ── Load DB URL from config ─────────────────────────────────────────
_settings = get_settings()
DATABASE_URL: str = os.getenv("DATABASE_URL", _settings.database_url)

# Render and Neon Postgres provide URLs starting with postgres://, which SQLAlchemy requires as postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ── Engine setup ─────────────────────────────────────────────────────
# For SQLite we need check_same_thread=False (FastAPI uses threads).
# For PostgreSQL this kwarg is ignored automatically.
_connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    # Ensure local directory for SQLite file exists
    if "///" in DATABASE_URL:
        db_file_str = DATABASE_URL.split("///", 1)[1]
        db_file_path = Path(db_file_str)
        if db_file_path.parent and str(db_file_path.parent) != ".":
            db_file_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args=_connect_args,
    echo=False,           # set True to log every SQL statement
    pool_pre_ping=True,   # reconnect on stale connections
)

# Enable WAL mode and foreign keys for SQLite (better concurrency)
if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):  # type: ignore
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


# ── Session factory ──────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# ── Declarative Base ─────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared base class for all ORM models."""
    pass


# ── Dependency for FastAPI ───────────────────────────────────────────
def get_db() -> Session:  # type: ignore[misc]
    """
    FastAPI dependency that yields a DB session and closes it afterwards.

    Usage in a router:
        @router.get("/machines")
        def list_machines(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db  # type: ignore[misc]
    finally:
        db.close()


# ── Table creation helper ───────────────────────────────────────────
def create_all_tables() -> None:
    """
    Create every table defined in Base.metadata.
    Called once at app startup (main.py) or by init_db.py.
    """
    # Import all model modules so Base.metadata knows about them
    import backend.models  # noqa: F401  (side-effect import)
    Base.metadata.create_all(bind=engine)
    print("✅ All database tables created / verified.")

