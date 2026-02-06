"""
Database connection and session management.

Simple setup:
- get_engine() - creates SQLAlchemy engine
- get_session() - creates a session for database operations
- init_db() - creates all tables
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from floating_prompts.config import get_settings
from floating_prompts.models import Base

# Module-level engine (lazy initialized)
_engine: Engine | None = None


def get_engine() -> Engine:
    """
    Get or create the SQLAlchemy engine.

    Uses connection pooling by default.
    """
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,  # Verify connections before use
            echo=False,  # Set to True for SQL debugging
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Get a session factory bound to the engine."""
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Handles commit/rollback automatically.

    Usage:
        with get_session() as session:
            prompt = Prompt(name="test", version=1, user_prompt="Hello")
            session.add(prompt)
            # Auto-commits on exit, rolls back on exception
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """
    Create all database tables.

    Safe to call multiple times - only creates tables that don't exist.
    """
    Base.metadata.create_all(get_engine())


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This deletes all data. Use with caution.
    """
    Base.metadata.drop_all(get_engine())
