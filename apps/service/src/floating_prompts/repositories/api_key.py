"""API key repository."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select

from floating_prompts.models.api_key import ApiKey
from floating_prompts.repositories.base import AsyncRepository

__all__ = ["ApiKeyRepository"]


class ApiKeyRepository(AsyncRepository[ApiKey]):
    """Data access for :class:`ApiKey`."""

    model = ApiKey

    async def get_by_prefix(self, prefix: str) -> ApiKey | None:
        """Return a key by its indexable prefix (used during authentication)."""
        stmt = select(ApiKey).where(ApiKey.prefix == prefix)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_project(self, project_id: int) -> Sequence[ApiKey]:
        """Return all keys belonging to a project."""
        stmt = (
            select(ApiKey)
            .where(ApiKey.project_id == project_id)
            .order_by(ApiKey.created_at)
        )
        return (await self.session.execute(stmt)).scalars().all()
