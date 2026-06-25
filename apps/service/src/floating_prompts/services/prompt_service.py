"""Prompt service — prompts, immutable versions, tags, and rendering.

This is the heart of the domain. It owns the rules the data model cannot
express on its own: monotonic version numbering, tag (alias) movement, and
validated rendering.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from floating_prompts.core.exceptions import ConflictError, NotFoundError
from floating_prompts.models.prompt import Prompt, PromptVersion, Tag
from floating_prompts.repositories.project import ProjectRepository
from floating_prompts.repositories.prompt import PromptRepository
from floating_prompts.services.base import BaseService
from floating_prompts.services.rendering import RenderedPrompt, TemplateRenderer

__all__ = ["PromptService"]


def _checksum(
    system_prompt: str | None, user_prompt: str, variables: list[dict[str, Any]]
) -> str:
    """Stable content hash for a prompt version (dedup / change detection)."""
    payload = json.dumps(
        {
            "system": system_prompt,
            "user": user_prompt,
            "variables": sorted(variables, key=lambda v: str(v.get("name"))),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class PromptService(BaseService):
    """Business logic for the prompt aggregate."""

    def __init__(
        self, session: AsyncSession, *, renderer: TemplateRenderer | None = None
    ) -> None:
        super().__init__(session)
        self._projects = ProjectRepository(session)
        self._prompts = PromptRepository(session)
        self._renderer = renderer or TemplateRenderer()

    # -- Prompt identity -----------------------------------------------------

    async def _project_id(self, project_slug: str) -> int:
        project = await self._projects.get_by_slug(project_slug)
        if project is None:
            raise NotFoundError(
                f"Project '{project_slug}' not found.",
                extra={"slug": project_slug},
            )
        return project.id

    async def create_prompt(
        self,
        *,
        project_slug: str,
        name: str,
        description: str | None,
        actor: str,
    ) -> Prompt:
        """Create a prompt identity within a project."""
        project_id = await self._project_id(project_slug)
        if await self._prompts.get_by_name(project_id, name) is not None:
            raise ConflictError(
                f"Prompt '{name}' already exists in project '{project_slug}'.",
                extra={"project": project_slug, "name": name},
            )
        prompt = await self._prompts.add(
            Prompt(project_id=project_id, name=name, description=description)
        )
        await self._record(
            actor=actor,
            action="prompt.create",
            resource_type="prompt",
            resource_id=f"{project_slug}/{name}",
        )
        return prompt

    async def get_prompt(self, *, project_slug: str, name: str) -> Prompt:
        """Return a prompt or raise ``NotFoundError``."""
        project_id = await self._project_id(project_slug)
        prompt = await self._prompts.get_by_name(project_id, name)
        if prompt is None:
            raise NotFoundError(
                f"Prompt '{name}' not found in project '{project_slug}'.",
                extra={"project": project_slug, "name": name},
            )
        return prompt

    async def list_prompts(
        self, *, project_slug: str, limit: int = 50, offset: int = 0
    ) -> tuple[Sequence[Prompt], int]:
        """Return a page of prompts in a project and the total count."""
        project_id = await self._project_id(project_slug)
        items = await self._prompts.list_for_project(
            project_id, limit=limit, offset=offset
        )
        total = await self._prompts.count_for_project(project_id)
        return items, total

    async def delete_prompt(self, *, project_slug: str, name: str, actor: str) -> None:
        """Delete a prompt and all of its versions and tags."""
        prompt = await self.get_prompt(project_slug=project_slug, name=name)
        await self._prompts.delete(prompt)
        await self._record(
            actor=actor,
            action="prompt.delete",
            resource_type="prompt",
            resource_id=f"{project_slug}/{name}",
        )

    # -- Versions ------------------------------------------------------------

    async def create_version(
        self,
        *,
        project_slug: str,
        name: str,
        user_prompt: str,
        system_prompt: str | None = None,
        variables: list[dict[str, Any]] | None = None,
        actor: str,
        create_prompt_if_missing: bool = True,
    ) -> PromptVersion:
        """Append a new immutable version, auto-incrementing the version number.

        If ``variables`` is omitted, the declared contract is inferred from the
        variables referenced in the templates (all treated as required).
        """
        prompt = await self._get_or_create_prompt(
            project_slug=project_slug,
            name=name,
            create_if_missing=create_prompt_if_missing,
            actor=actor,
        )

        if variables is None:
            referenced = self._renderer.referenced_variables(system_prompt, user_prompt)
            variables = [
                {"name": var, "required": True, "description": None}
                for var in sorted(referenced)
            ]

        next_version = await self._prompts.next_version_number(prompt.id)
        version = await self._prompts.add_version(
            PromptVersion(
                prompt_id=prompt.id,
                version=next_version,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                variables=variables,
                checksum=_checksum(system_prompt, user_prompt, variables),
                created_by=actor,
            )
        )
        await self._record(
            actor=actor,
            action="version.create",
            resource_type="prompt_version",
            resource_id=f"{project_slug}/{name}@{next_version}",
            details={"version": next_version},
        )
        return version

    async def _get_or_create_prompt(
        self, *, project_slug: str, name: str, create_if_missing: bool, actor: str
    ) -> Prompt:
        project_id = await self._project_id(project_slug)
        prompt = await self._prompts.get_by_name(project_id, name)
        if prompt is not None:
            return prompt
        if not create_if_missing:
            raise NotFoundError(
                f"Prompt '{name}' not found in project '{project_slug}'.",
                extra={"project": project_slug, "name": name},
            )
        return await self.create_prompt(
            project_slug=project_slug, name=name, description=None, actor=actor
        )

    async def list_versions(
        self, *, project_slug: str, name: str
    ) -> Sequence[PromptVersion]:
        """Return all versions of a prompt, newest first."""
        prompt = await self.get_prompt(project_slug=project_slug, name=name)
        return await self._prompts.list_versions(prompt.id)

    async def resolve(
        self,
        *,
        project_slug: str,
        name: str,
        version: int | None = None,
        tag: str | None = None,
    ) -> PromptVersion:
        """Resolve a prompt to a concrete version.

        Resolution precedence: explicit ``version`` → ``tag`` alias → latest.
        """
        prompt = await self.get_prompt(project_slug=project_slug, name=name)

        if version is not None:
            resolved = await self._prompts.get_version(prompt.id, version)
            if resolved is None:
                raise NotFoundError(
                    f"Version {version} of '{name}' not found.",
                    extra={"project": project_slug, "name": name, "version": version},
                )
            return resolved

        if tag is not None:
            tag_row = await self._prompts.get_tag(prompt.id, tag)
            if tag_row is None:
                raise NotFoundError(
                    f"Tag '{tag}' not found on prompt '{name}'.",
                    extra={"project": project_slug, "name": name, "tag": tag},
                )
            return await self._require_version(prompt.id, tag_row.version_id)

        latest = await self._prompts.get_latest_version(prompt.id)
        if latest is None:
            raise NotFoundError(
                f"Prompt '{name}' has no versions yet.",
                extra={"project": project_slug, "name": name},
            )
        return latest

    async def _require_version(self, prompt_id: int, version_id: int) -> PromptVersion:
        version = await self.session.get(PromptVersion, version_id)
        if version is None or version.prompt_id != prompt_id:
            raise NotFoundError("Referenced prompt version no longer exists.")
        return version

    # -- Tags ----------------------------------------------------------------

    async def set_tag(
        self,
        *,
        project_slug: str,
        name: str,
        tag_name: str,
        version: int,
        actor: str,
    ) -> Tag:
        """Create or move a tag to point at a specific version."""
        prompt = await self.get_prompt(project_slug=project_slug, name=name)
        target = await self._prompts.get_version(prompt.id, version)
        if target is None:
            raise NotFoundError(
                f"Version {version} of '{name}' not found.",
                extra={"project": project_slug, "name": name, "version": version},
            )

        tag = await self._prompts.get_tag(prompt.id, tag_name)
        if tag is None:
            tag = await self._prompts.add_tag(
                Tag(prompt_id=prompt.id, name=tag_name, version_id=target.id)
            )
        else:
            tag.version_id = target.id
            await self.session.flush()

        await self._record(
            actor=actor,
            action="tag.set",
            resource_type="tag",
            resource_id=f"{project_slug}/{name}:{tag_name}",
            details={"version": version},
        )
        return tag

    async def list_tags(self, *, project_slug: str, name: str) -> Sequence[Tag]:
        """Return all tags of a prompt."""
        prompt = await self.get_prompt(project_slug=project_slug, name=name)
        return await self._prompts.list_tags(prompt.id)

    async def delete_tag(
        self, *, project_slug: str, name: str, tag_name: str, actor: str
    ) -> None:
        """Remove a tag (does not affect the version it pointed at)."""
        prompt = await self.get_prompt(project_slug=project_slug, name=name)
        tag = await self._prompts.get_tag(prompt.id, tag_name)
        if tag is None:
            raise NotFoundError(
                f"Tag '{tag_name}' not found on prompt '{name}'.",
                extra={"project": project_slug, "name": name, "tag": tag_name},
            )
        await self.session.delete(tag)
        await self._record(
            actor=actor,
            action="tag.delete",
            resource_type="tag",
            resource_id=f"{project_slug}/{name}:{tag_name}",
        )

    # -- Rendering -----------------------------------------------------------

    async def render(
        self,
        *,
        project_slug: str,
        name: str,
        values: dict[str, object],
        version: int | None = None,
        tag: str | None = None,
    ) -> tuple[PromptVersion, RenderedPrompt]:
        """Resolve a version and render it with the supplied variable values."""
        resolved = await self.resolve(
            project_slug=project_slug, name=name, version=version, tag=tag
        )
        declared = {str(spec["name"]) for spec in resolved.variables}
        required = {
            str(spec["name"])
            for spec in resolved.variables
            if spec.get("required", True)
        }
        rendered = self._renderer.render(
            system_prompt=resolved.system_prompt,
            user_prompt=resolved.user_prompt,
            declared=declared,
            required=required,
            values=values,
        )
        return resolved, rendered
