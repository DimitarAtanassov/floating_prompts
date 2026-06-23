"""API key service — issuing, authenticating, and revoking credentials."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from floating_prompts.core import security
from floating_prompts.core.config import AppSettings, get_settings
from floating_prompts.core.exceptions import AuthenticationError, NotFoundError
from floating_prompts.models.api_key import ApiKey
from floating_prompts.repositories.api_key import ApiKeyRepository
from floating_prompts.repositories.project import ProjectRepository
from floating_prompts.services.base import BaseService

__all__ = ["ApiKeyService", "IssuedApiKey"]


@dataclass(frozen=True, slots=True)
class IssuedApiKey:
    """A newly created key plus the one-time plaintext to show the caller."""

    api_key: ApiKey
    plaintext: str


class ApiKeyService(BaseService):
    """Business logic for API-key lifecycle and authentication."""

    def __init__(
        self, session: AsyncSession, *, settings: AppSettings | None = None
    ) -> None:
        super().__init__(session)
        self._keys = ApiKeyRepository(session)
        self._projects = ProjectRepository(session)
        self._settings = settings or get_settings()

    async def issue(
        self,
        *,
        name: str,
        scopes: list[str],
        project_slug: str | None,
        expires_at: datetime | None,
        actor: str,
    ) -> IssuedApiKey:
        """Mint a new key, persisting only its prefix and hash."""
        project_id: int | None = None
        if project_slug is not None:
            project = await self._projects.get_by_slug(project_slug)
            if project is None:
                raise NotFoundError(
                    f"Project '{project_slug}' not found.",
                    extra={"slug": project_slug},
                )
            project_id = project.id

        generated = security.generate_api_key(self._settings.auth.key_prefix_length)
        api_key = await self._keys.add(
            ApiKey(
                project_id=project_id,
                name=name,
                prefix=generated.prefix,
                token_hash=generated.token_hash,
                scopes=scopes,
                expires_at=expires_at,
            )
        )
        await self._record(
            actor=actor,
            action="api_key.issue",
            resource_type="api_key",
            resource_id=generated.prefix,
            details={"scopes": scopes, "project": project_slug},
        )
        return IssuedApiKey(api_key=api_key, plaintext=generated.plaintext)

    async def authenticate(self, presented: str) -> ApiKey:
        """Resolve a presented key string to a valid, active ``ApiKey``.

        Raises ``AuthenticationError`` for unknown, mismatched, revoked, or
        expired keys. Updates ``last_used_at`` on success.
        """
        prefix = security.extract_prefix(
            presented, self._settings.auth.key_prefix_length
        )
        api_key = await self._keys.get_by_prefix(prefix)
        if api_key is None or not security.verify_token(presented, api_key.token_hash):
            raise AuthenticationError("Invalid API key.")

        now = datetime.now(UTC)
        if api_key.revoked_at is not None:
            raise AuthenticationError("API key has been revoked.")
        if api_key.expires_at is not None and api_key.expires_at <= now:
            raise AuthenticationError("API key has expired.")

        api_key.last_used_at = now
        await self.session.flush()
        return api_key

    async def list_for_project(self, *, project_slug: str) -> Sequence[ApiKey]:
        """List keys belonging to a project."""
        project = await self._projects.get_by_slug(project_slug)
        if project is None:
            raise NotFoundError(
                f"Project '{project_slug}' not found.", extra={"slug": project_slug}
            )
        return await self._keys.list_for_project(project.id)

    async def revoke(self, *, key_id: int, actor: str) -> ApiKey:
        """Revoke a key by id."""
        api_key = await self._keys.get(key_id)
        if api_key is None:
            raise NotFoundError(f"API key {key_id} not found.")
        api_key.revoked_at = datetime.now(UTC)
        await self.session.flush()
        await self._record(
            actor=actor,
            action="api_key.revoke",
            resource_type="api_key",
            resource_id=api_key.prefix,
        )
        return api_key
