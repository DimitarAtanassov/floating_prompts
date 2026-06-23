"""Prompt, version, tag, and rendering schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "PromptCreate",
    "PromptRead",
    "PromptVersionCreate",
    "PromptVersionRead",
    "RenderRequest",
    "RenderResult",
    "TagRead",
    "TagSet",
    "VariableSpec",
]

NAME_PATTERN = r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,254}$"
TAG_PATTERN = r"^[a-z0-9][a-z0-9._-]{0,63}$"


class VariableSpec(BaseModel):
    """A declared template variable."""

    name: str = Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$", examples=["content"])
    required: bool = True
    description: str | None = None


class PromptCreate(BaseModel):
    """Payload for creating a prompt identity."""

    name: str = Field(pattern=NAME_PATTERN, examples=["summarizer"])
    description: str | None = Field(default=None, max_length=2000)


class PromptRead(BaseModel):
    """Prompt identity as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class PromptVersionCreate(BaseModel):
    """Payload for creating a new prompt version.

    If ``variables`` is omitted, the declared contract is inferred from the
    variables referenced in the templates.
    """

    user_prompt: str = Field(
        min_length=1, examples=["Summarize the following:\n\n{{ content }}"]
    )
    system_prompt: str | None = Field(
        default=None, examples=["You are a concise assistant."]
    )
    variables: list[VariableSpec] | None = None


class PromptVersionRead(BaseModel):
    """A prompt version as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt_id: int
    version: int
    system_prompt: str | None
    user_prompt: str
    variables: list[VariableSpec]
    checksum: str
    created_by: str | None
    created_at: datetime


class TagSet(BaseModel):
    """Payload for pointing a tag at a version."""

    version: int = Field(ge=1, examples=[1])


class TagRead(BaseModel):
    """A tag (alias) as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    version_id: int
    created_at: datetime
    updated_at: datetime


class RenderRequest(BaseModel):
    """Payload for rendering a prompt with variable values."""

    variables: dict[str, Any] = Field(default_factory=dict)
    version: int | None = Field(default=None, ge=1)
    tag: str | None = Field(default=None, pattern=TAG_PATTERN)


class RenderResult(BaseModel):
    """The result of rendering a prompt version."""

    name: str
    version: int
    system_prompt: str | None
    user_prompt: str
