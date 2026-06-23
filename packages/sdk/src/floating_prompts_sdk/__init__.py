"""Floating Prompts SDK.

A standalone, typed Python client for the Floating Prompts API, plus the Pydantic
schemas and the ``Scope`` enum that define the API contract. Depends only on
``pydantic`` and ``httpx`` — no server-side dependencies.

Example:
    >>> from floating_prompts_sdk import PromptsClient
    >>> with PromptsClient("http://localhost:8000", api_key="fp_...") as c:
    ...     c.render("acme", "summarizer", {"content": "..."}, tag="production")
"""

from __future__ import annotations

from floating_prompts_sdk.client import (
    AsyncPromptsClient,
    PromptsClient,
    PromptsClientError,
)
from floating_prompts_sdk.schemas import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyRead,
    Page,
    PageMeta,
    ProblemDetail,
    ProjectCreate,
    ProjectRead,
    PromptCreate,
    PromptRead,
    PromptVersionCreate,
    PromptVersionRead,
    RenderRequest,
    RenderResult,
    TagRead,
    TagSet,
    VariableSpec,
)
from floating_prompts_sdk.scopes import Scope

__all__ = [
    "ApiKeyCreate",
    "ApiKeyCreated",
    "ApiKeyRead",
    "AsyncPromptsClient",
    "Page",
    "PageMeta",
    "ProblemDetail",
    "ProjectCreate",
    "ProjectRead",
    "PromptCreate",
    "PromptRead",
    "PromptVersionCreate",
    "PromptVersionRead",
    "PromptsClient",
    "PromptsClientError",
    "RenderRequest",
    "RenderResult",
    "Scope",
    "TagRead",
    "TagSet",
    "VariableSpec",
    "__version__",
]

__version__ = "0.1.0"
