"""Project endpoints."""

from __future__ import annotations

from fastapi import APIRouter, status

from floating_prompts.api.deps import PaginationDep, ProjectServiceDep
from floating_prompts_sdk.schemas.common import Page
from floating_prompts_sdk.schemas.project import ProjectCreate, ProjectRead

__all__ = ["router"]

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a project")
async def create_project(
    payload: ProjectCreate, service: ProjectServiceDep
) -> ProjectRead:
    project = await service.create(
        slug=payload.slug,
        name=payload.name,
        description=payload.description,
    )
    return ProjectRead.model_validate(project)


@router.get("", summary="List projects")
async def list_projects(
    service: ProjectServiceDep, pagination: PaginationDep
) -> Page[ProjectRead]:
    items, total = await service.list(limit=pagination.limit, offset=pagination.offset)
    return Page.of(
        [ProjectRead.model_validate(p) for p in items],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get("/{slug}", summary="Get a project")
async def get_project(slug: str, service: ProjectServiceDep) -> ProjectRead:
    project = await service.get(slug)
    return ProjectRead.model_validate(project)


@router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
)
async def delete_project(slug: str, service: ProjectServiceDep) -> None:
    await service.delete(slug=slug)
