"""Shared service base: holds the unit of work (the async session)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["BaseService"]


class BaseService:
    """Base class giving services access to the request-scoped session."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
