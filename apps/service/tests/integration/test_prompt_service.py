"""Integration tests for the prompt service against a real database."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from floating_prompts.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from floating_prompts.services.project_service import ProjectService
from floating_prompts.services.prompt_service import PromptService

pytestmark = pytest.mark.integration


@pytest.fixture
async def project(session: AsyncSession) -> str:
    await ProjectService(session).create(slug="acme", name="ACME", description=None)
    return "acme"


async def test_versions_auto_increment(session: AsyncSession, project: str) -> None:
    service = PromptService(session)
    v1 = await service.create_version(
        project_slug=project, name="p", user_prompt="{{ a }}"
    )
    v2 = await service.create_version(
        project_slug=project, name="p", user_prompt="{{ a }} {{ b }}"
    )
    assert (v1.version, v2.version) == (1, 2)
    # Variables inferred from the template.
    assert {spec["name"] for spec in v2.variables} == {"a", "b"}


async def test_resolution_precedence(session: AsyncSession, project: str) -> None:
    service = PromptService(session)
    await service.create_version(project_slug=project, name="p", user_prompt="one")
    await service.create_version(project_slug=project, name="p", user_prompt="two")
    await service.set_tag(
        project_slug=project, name="p", tag_name="production", version=1
    )

    # Default → latest.
    assert (await service.resolve(project_slug=project, name="p")).version == 2
    # Tag → its target.
    by_tag = await service.resolve(project_slug=project, name="p", tag="production")
    assert by_tag.version == 1
    # Explicit version wins.
    by_ver = await service.resolve(project_slug=project, name="p", version=1)
    assert by_ver.version == 1


async def test_moving_a_tag(session: AsyncSession, project: str) -> None:
    service = PromptService(session)
    await service.create_version(project_slug=project, name="p", user_prompt="one")
    await service.create_version(project_slug=project, name="p", user_prompt="two")
    await service.set_tag(project_slug=project, name="p", tag_name="prod", version=1)
    await service.set_tag(project_slug=project, name="p", tag_name="prod", version=2)
    assert (
        await service.resolve(project_slug=project, name="p", tag="prod")
    ).version == 2


async def test_render_missing_variable(session: AsyncSession, project: str) -> None:
    service = PromptService(session)
    await service.create_version(
        project_slug=project, name="p", user_prompt="Hi {{ name }}"
    )
    with pytest.raises(ValidationError):
        await service.render(project_slug=project, name="p", values={})


async def test_duplicate_prompt_conflict(session: AsyncSession, project: str) -> None:
    service = PromptService(session)
    await service.create_prompt(project_slug=project, name="p", description=None)
    with pytest.raises(ConflictError):
        await service.create_prompt(project_slug=project, name="p", description=None)


async def test_unknown_project_raises(session: AsyncSession) -> None:
    with pytest.raises(NotFoundError):
        await PromptService(session).create_version(
            project_slug="ghost", name="p", user_prompt="x"
        )
