"""API key schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from floating_prompts_sdk.scopes import Scope

__all__ = ["ApiKeyCreate", "ApiKeyCreated", "ApiKeyRead"]


class ApiKeyCreate(BaseModel):
    """Payload for issuing an API key."""

    name: str = Field(min_length=1, max_length=255, examples=["ci-pipeline"])
    scopes: list[Scope] = Field(
        default_factory=lambda: [Scope.READ], examples=[["read", "write"]]
    )
    project_slug: str | None = Field(
        default=None,
        description="Scope the key to a project; omit for a global key.",
    )
    expires_at: datetime | None = None


class ApiKeyRead(BaseModel):
    """API key metadata (never includes the secret)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prefix: str
    scopes: list[str]
    project_id: int | None
    last_used_at: datetime | None
    expires_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime


class ApiKeyCreated(ApiKeyRead):
    """Response returned once at creation, including the one-time secret."""

    key: str = Field(description="The full API key — shown only once.")
