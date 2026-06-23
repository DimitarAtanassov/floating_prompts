"""Project repository."""

from __future__ import annotations

from sqlalchemy import select

from floating_prompts.models.project import Project
from floating_prompts.repositories.base import AsyncRepository

__all__ = ["ProjectRepository"]


class ProjectRepository(AsyncRepository[Project]):
    """Data access for :class:`Project`."""

    model = Project

    async def get_by_slug(self, slug: str) -> Project | None:
        """Return a project by its unique slug, or ``None``."""
        stmt = select(Project).where(Project.slug == slug)
        return (await self.session.execute(stmt)).scalar_one_or_none()
