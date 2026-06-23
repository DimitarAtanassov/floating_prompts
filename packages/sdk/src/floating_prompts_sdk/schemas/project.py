"""Project request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

__all__ = ["ProjectCreate", "ProjectRead"]

SLUG_PATTERN = r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$"


class ProjectCreate(BaseModel):
    """Payload for creating a project."""

    slug: str = Field(
        pattern=SLUG_PATTERN,
        description="URL-safe identifier (lowercase letters, digits, hyphens).",
        examples=["acme-support"],
    )
    name: str = Field(min_length=1, max_length=255, examples=["ACME Support"])
    description: str | None = Field(default=None, max_length=2000)


class ProjectRead(BaseModel):
    """Project as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
