"""Async engine and session management.

The engine and sessionmaker are created lazily and cached at module level so the
whole process shares one connection pool. ``session_scope`` is a transactional
context manager (commit on success, rollback on error); the FastAPI request
dependency in :mod:`floating_prompts.api.deps` builds on the same sessionmaker.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from floating_prompts.core.config import AppSettings, get_settings

__all__ = [
    "dispose_engine",
    "get_engine",
    "get_sessionmaker",
    "session_scope",
]

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: AppSettings | None = None) -> AsyncEngine:
    """Return the process-wide async engine, creating it on first use."""
    global _engine  # noqa: PLW0603
    if _engine is None:
        settings = settings or get_settings()
        _engine = create_async_engine(
            settings.db.async_url,
            echo=settings.db.echo,
            pool_pre_ping=settings.db.pool_pre_ping,
            pool_size=settings.db.pool_size,
            max_overflow=settings.db.max_overflow,
        )
    return _engine


def get_sessionmaker(
    settings: AppSettings | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Return the process-wide session factory."""
    global _sessionmaker  # noqa: PLW0603
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(
            bind=get_engine(settings),
            expire_on_commit=False,
            autoflush=False,
        )
    return _sessionmaker


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Provide a transactional session scope.

    Commits on clean exit, rolls back on exception, always closes.
    """
    session = get_sessionmaker()()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def dispose_engine() -> None:
    """Dispose the engine's connection pool (call on shutdown)."""
    global _engine, _sessionmaker  # noqa: PLW0603
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
