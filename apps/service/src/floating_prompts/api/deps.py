"""FastAPI dependencies: sessions, services, and pagination.

Wiring lives here so routers stay declarative and everything is overridable in
tests via ``app.dependency_overrides``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from floating_prompts.db.session import get_sessionmaker
from floating_prompts.services.project_service import ProjectService
from floating_prompts.services.prompt_service import PromptService

__all__ = [
    "Pagination",
    "PaginationDep",
    "ProjectServiceDep",
    "PromptServiceDep",
    "SessionDep",
    "get_session",
]


async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide a request-scoped session, committing on success."""
    async with get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


SessionDep = Annotated[AsyncSession, Depends(get_session)]


# -- Service providers -------------------------------------------------------


def get_project_service(session: SessionDep) -> ProjectService:
    return ProjectService(session)


def get_prompt_service(session: SessionDep) -> PromptService:
    return PromptService(session)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
PromptServiceDep = Annotated[PromptService, Depends(get_prompt_service)]


# -- Pagination --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Pagination:
    """Validated pagination parameters."""

    limit: int
    offset: int


def get_pagination(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Pagination:
    return Pagination(limit=limit, offset=offset)


PaginationDep = Annotated[Pagination, Depends(get_pagination)]
