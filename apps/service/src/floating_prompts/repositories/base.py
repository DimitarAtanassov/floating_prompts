"""Generic async repository.

Provides the CRUD operations every entity shares so concrete repositories only
add the queries specific to their aggregate (DRY). ``flush`` is used instead of
``commit`` so the owning unit of work controls transaction boundaries.
"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from floating_prompts.db.base import Base

__all__ = ["AsyncRepository"]


class AsyncRepository[ModelT: Base]:
    """Base repository with shared CRUD operations for one model."""

    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, entity_id: int) -> ModelT | None:
        """Return an entity by primary key, or ``None``."""
        return await self.session.get(self.model, entity_id)

    async def add(self, entity: ModelT) -> ModelT:
        """Stage a new entity and flush to populate generated columns."""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Mark an entity for deletion."""
        await self.session.delete(entity)

    async def list(self, *, limit: int = 50, offset: int = 0) -> Sequence[ModelT]:
        """Return a page of entities ordered by primary key."""
        stmt = (
            select(self.model)
            .order_by(self.model.id)  # type: ignore[attr-defined]
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self) -> int:
        """Return the total number of entities."""
        stmt = select(func.count()).select_from(self.model)
        return (await self.session.execute(stmt)).scalar_one()
