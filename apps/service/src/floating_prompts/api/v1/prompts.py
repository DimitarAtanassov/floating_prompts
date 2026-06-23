"""Prompt, version, and tag endpoints (nested under a project)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from floating_prompts.api.deps import (
    AuthContext,
    PaginationDep,
    PromptServiceDep,
    require_scope,
)
from floating_prompts.models.api_key import Scope
from floating_prompts_sdk.schemas.common import Page
from floating_prompts_sdk.schemas.prompt import (
    PromptCreate,
    PromptRead,
    PromptVersionCreate,
    PromptVersionRead,
    TagRead,
    TagSet,
)

__all__ = ["router"]

router = APIRouter(prefix="/projects/{slug}/prompts", tags=["prompts"])

WriteAuth = Annotated[AuthContext, Depends(require_scope(Scope.WRITE))]
ReadAuth = Annotated[AuthContext, Depends(require_scope(Scope.READ))]


# -- Prompts -----------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a prompt")
async def create_prompt(
    slug: str, payload: PromptCreate, service: PromptServiceDep, auth: WriteAuth
) -> PromptRead:
    prompt = await service.create_prompt(
        project_slug=slug,
        name=payload.name,
        description=payload.description,
        actor=auth.actor,
    )
    return PromptRead.model_validate(prompt)


@router.get("", summary="List prompts in a project")
async def list_prompts(
    slug: str,
    service: PromptServiceDep,
    pagination: PaginationDep,
    _: ReadAuth,
) -> Page[PromptRead]:
    items, total = await service.list_prompts(
        project_slug=slug, limit=pagination.limit, offset=pagination.offset
    )
    return Page.of(
        [PromptRead.model_validate(p) for p in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/{name}", summary="Get a prompt")
async def get_prompt(
    slug: str, name: str, service: PromptServiceDep, _: ReadAuth
) -> PromptRead:
    prompt = await service.get_prompt(project_slug=slug, name=name)
    return PromptRead.model_validate(prompt)


@router.delete(
    "/{name}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a prompt"
)
async def delete_prompt(
    slug: str, name: str, service: PromptServiceDep, auth: WriteAuth
) -> None:
    await service.delete_prompt(project_slug=slug, name=name, actor=auth.actor)


# -- Versions ----------------------------------------------------------------


@router.post(
    "/{name}/versions",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new prompt version",
)
async def create_version(
    slug: str,
    name: str,
    payload: PromptVersionCreate,
    service: PromptServiceDep,
    auth: WriteAuth,
) -> PromptVersionRead:
    version = await service.create_version(
        project_slug=slug,
        name=name,
        user_prompt=payload.user_prompt,
        system_prompt=payload.system_prompt,
        variables=(
            [v.model_dump() for v in payload.variables]
            if payload.variables is not None
            else None
        ),
        actor=auth.actor,
    )
    return PromptVersionRead.model_validate(version)


@router.get("/{name}/versions", summary="List prompt versions")
async def list_versions(
    slug: str, name: str, service: PromptServiceDep, _: ReadAuth
) -> list[PromptVersionRead]:
    versions = await service.list_versions(project_slug=slug, name=name)
    return [PromptVersionRead.model_validate(v) for v in versions]


@router.get(
    "/{name}/resolve",
    summary="Resolve a prompt to a concrete version",
)
async def resolve_version(
    slug: str,
    name: str,
    service: PromptServiceDep,
    _: ReadAuth,
    version: Annotated[int | None, Query(ge=1)] = None,
    tag: Annotated[str | None, Query()] = None,
) -> PromptVersionRead:
    resolved = await service.resolve(
        project_slug=slug, name=name, version=version, tag=tag
    )
    return PromptVersionRead.model_validate(resolved)


# -- Tags --------------------------------------------------------------------


@router.put("/{name}/tags/{tag_name}", summary="Create or move a tag")
async def set_tag(  # noqa: PLR0913 - path params + body + deps
    slug: str,
    name: str,
    tag_name: str,
    payload: TagSet,
    service: PromptServiceDep,
    auth: WriteAuth,
) -> TagRead:
    tag = await service.set_tag(
        project_slug=slug,
        name=name,
        tag_name=tag_name,
        version=payload.version,
        actor=auth.actor,
    )
    return TagRead.model_validate(tag)


@router.get("/{name}/tags", summary="List tags")
async def list_tags(
    slug: str, name: str, service: PromptServiceDep, _: ReadAuth
) -> list[TagRead]:
    tags = await service.list_tags(project_slug=slug, name=name)
    return [TagRead.model_validate(t) for t in tags]


@router.delete(
    "/{name}/tags/{tag_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a tag",
)
async def delete_tag(
    slug: str,
    name: str,
    tag_name: str,
    service: PromptServiceDep,
    auth: WriteAuth,
) -> None:
    await service.delete_tag(
        project_slug=slug, name=name, tag_name=tag_name, actor=auth.actor
    )
