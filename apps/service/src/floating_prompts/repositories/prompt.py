"""Prompt repository — prompts, their versions, and tags."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import desc, func, select

from floating_prompts.models.prompt import Prompt, PromptVersion, Tag
from floating_prompts.repositories.base import AsyncRepository

__all__ = ["PromptRepository"]


class PromptRepository(AsyncRepository[Prompt]):
    """Data access for the prompt aggregate (prompt + versions + tags)."""

    model = Prompt

    # -- Prompts -------------------------------------------------------------

    async def get_by_name(self, project_id: int, name: str) -> Prompt | None:
        """Return a prompt by name within a project."""
        stmt = select(Prompt).where(
            Prompt.project_id == project_id, Prompt.name == name
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_project(
        self, project_id: int, *, limit: int = 50, offset: int = 0
    ) -> Sequence[Prompt]:
        """Return a page of prompts in a project, ordered by name."""
        stmt = (
            select(Prompt)
            .where(Prompt.project_id == project_id)
            .order_by(Prompt.name)
            .limit(limit)
            .offset(offset)
        )
        return (await self.session.execute(stmt)).scalars().all()

    async def count_for_project(self, project_id: int) -> int:
        """Count prompts in a project."""
        stmt = (
            select(func.count())
            .select_from(Prompt)
            .where(Prompt.project_id == project_id)
        )
        return (await self.session.execute(stmt)).scalar_one()

    async def add_version(self, version: PromptVersion) -> PromptVersion:
        """Stage and flush a new prompt version."""
        self.session.add(version)
        await self.session.flush()
        return version

    async def add_tag(self, tag: Tag) -> Tag:
        """Stage and flush a new tag."""
        self.session.add(tag)
        await self.session.flush()
        return tag

    # -- Versions ------------------------------------------------------------

    async def get_version(self, prompt_id: int, version: int) -> PromptVersion | None:
        """Return a specific version of a prompt."""
        stmt = select(PromptVersion).where(
            PromptVersion.prompt_id == prompt_id,
            PromptVersion.version == version,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_latest_version(self, prompt_id: int) -> PromptVersion | None:
        """Return the highest-numbered version of a prompt."""
        stmt = (
            select(PromptVersion)
            .where(PromptVersion.prompt_id == prompt_id)
            .order_by(desc(PromptVersion.version))
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def next_version_number(self, prompt_id: int) -> int:
        """Return the next monotonic version number for a prompt."""
        stmt = select(func.max(PromptVersion.version)).where(
            PromptVersion.prompt_id == prompt_id
        )
        current = (await self.session.execute(stmt)).scalar()
        return (current or 0) + 1

    async def list_versions(self, prompt_id: int) -> Sequence[PromptVersion]:
        """Return all versions of a prompt, newest first."""
        stmt = (
            select(PromptVersion)
            .where(PromptVersion.prompt_id == prompt_id)
            .order_by(desc(PromptVersion.version))
        )
        return (await self.session.execute(stmt)).scalars().all()

    # -- Tags ----------------------------------------------------------------

    async def get_tag(self, prompt_id: int, name: str) -> Tag | None:
        """Return a tag of a prompt by name."""
        stmt = select(Tag).where(Tag.prompt_id == prompt_id, Tag.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_tags(self, prompt_id: int) -> Sequence[Tag]:
        """Return all tags of a prompt, ordered by name."""
        stmt = select(Tag).where(Tag.prompt_id == prompt_id).order_by(Tag.name)
        return (await self.session.execute(stmt)).scalars().all()
