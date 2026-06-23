"""Audit log repository."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import desc, select

from floating_prompts.models.audit import AuditLog
from floating_prompts.repositories.base import AsyncRepository

__all__ = ["AuditRepository"]


class AuditRepository(AsyncRepository[AuditLog]):
    """Data access for :class:`AuditLog` (append-only)."""

    model = AuditLog

    async def list_recent(
        self, *, limit: int = 50, offset: int = 0
    ) -> Sequence[AuditLog]:
        """Return audit entries, newest first."""
        stmt = (
            select(AuditLog)
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.execute(stmt)).scalars().all()
