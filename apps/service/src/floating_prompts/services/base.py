"""Shared service base.

Holds the unit of work (the async session) and a single helper for emitting
audit records, so every concrete service records mutations the same way (DRY).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from floating_prompts.models.audit import AuditLog
from floating_prompts.repositories.audit import AuditRepository

__all__ = ["BaseService"]


class BaseService:
    """Base class providing the session and audit logging to services."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._audit = AuditRepository(session)

    async def _record(
        self,
        *,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Append an audit entry for a state-changing action."""
        await self._audit.add(
            AuditLog(
                actor=actor,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
            )
        )
