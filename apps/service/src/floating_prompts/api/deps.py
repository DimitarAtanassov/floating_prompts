"""FastAPI dependencies: sessions, services, authentication, and pagination.

Wiring lives here so routers stay declarative and everything is overridable in
tests via ``app.dependency_overrides``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from floating_prompts.core.config import AppSettings, get_settings
from floating_prompts.core.exceptions import AuthenticationError, AuthorizationError
from floating_prompts.db.session import get_sessionmaker
from floating_prompts.models.api_key import ApiKey, Scope
from floating_prompts.services.api_key_service import ApiKeyService
from floating_prompts.services.project_service import ProjectService
from floating_prompts.services.prompt_service import PromptService

__all__ = [
    "AuthContext",
    "Pagination",
    "get_session",
    "require_scope",
]

_settings = get_settings()
_api_key_scheme = APIKeyHeader(name=_settings.auth.api_key_header, auto_error=False)


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


def get_app_settings() -> AppSettings:
    return get_settings()


SettingsDep = Annotated[AppSettings, Depends(get_app_settings)]


# -- Service providers -------------------------------------------------------


def get_project_service(session: SessionDep) -> ProjectService:
    return ProjectService(session)


def get_prompt_service(session: SessionDep) -> PromptService:
    return PromptService(session)


def get_api_key_service(session: SessionDep, settings: SettingsDep) -> ApiKeyService:
    return ApiKeyService(session, settings=settings)


ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
PromptServiceDep = Annotated[PromptService, Depends(get_prompt_service)]
ApiKeyServiceDep = Annotated[ApiKeyService, Depends(get_api_key_service)]


# -- Authentication & authorization ------------------------------------------


@dataclass(frozen=True, slots=True)
class AuthContext:
    """The authenticated caller for the current request."""

    api_key: ApiKey

    @property
    def scopes(self) -> set[str]:
        return set(self.api_key.scopes)

    @property
    def actor(self) -> str:
        return f"{self.api_key.name}({self.api_key.prefix})"

    def has_scope(self, scope: Scope) -> bool:
        return Scope.ADMIN in self.scopes or scope in self.scopes


async def get_auth_context(
    service: ApiKeyServiceDep,
    presented: Annotated[str | None, Security(_api_key_scheme)],
) -> AuthContext:
    """Authenticate the request from its API-key header."""
    if not presented:
        raise AuthenticationError("Missing API key.")
    api_key = await service.authenticate(presented)
    return AuthContext(api_key=api_key)


AuthContextDep = Annotated[AuthContext, Depends(get_auth_context)]


def require_scope(scope: Scope) -> Callable[[AuthContext], AuthContext]:
    """Build a dependency that requires the caller to hold ``scope``."""

    def _dependency(auth: AuthContextDep) -> AuthContext:
        if not auth.has_scope(scope):
            raise AuthorizationError(
                f"This action requires the '{scope}' scope.",
                extra={"required_scope": scope, "granted": sorted(auth.scopes)},
            )
        return auth

    return _dependency


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
