"""Project service — lifecycle of project namespaces."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from floating_prompts.core.exceptions import ConflictError, NotFoundError
from floating_prompts.models.project import Project
from floating_prompts.repositories.project import ProjectRepository
from floating_prompts.services.base import BaseService

__all__ = ["ProjectService"]


class ProjectService(BaseService):
    """Business logic for creating and managing projects."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self._projects = ProjectRepository(session)

    async def create(self, *, slug: str, name: str, description: str | None) -> Project:
        """Create a project. Raises ``ConflictError`` if the slug is taken."""
        if await self._projects.get_by_slug(slug) is not None:
            raise ConflictError(
                f"Project '{slug}' already exists.",
                extra={"slug": slug},
            )
        return await self._projects.add(
            Project(slug=slug, name=name, description=description)
        )

    async def get(self, slug: str) -> Project:
        """Return a project or raise ``NotFoundError``."""
        project = await self._projects.get_by_slug(slug)
        if project is None:
            raise NotFoundError(f"Project '{slug}' not found.", extra={"slug": slug})
        return project

    async def list(
        self, *, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[Project], int]:
        """Return a page of projects and the total count."""
        items = await self._projects.list(limit=limit, offset=offset)
        total = await self._projects.count()
        return items, total

    async def delete(self, *, slug: str) -> None:
        """Delete a project and everything it owns."""
        project = await self.get(slug)
        await self._projects.delete(project)
