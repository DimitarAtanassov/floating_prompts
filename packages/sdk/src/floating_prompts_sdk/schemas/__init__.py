"""Pydantic v2 DTOs for the API and SDK.

Schemas are the transport contract and are intentionally separate from ORM
models: request bodies validate input, response models shape output, and
neither leaks SQLAlchemy internals to clients.
"""

from floating_prompts_sdk.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyRead,
)
from floating_prompts_sdk.schemas.common import Page, PageMeta, ProblemDetail
from floating_prompts_sdk.schemas.project import ProjectCreate, ProjectRead
from floating_prompts_sdk.schemas.prompt import (
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

__all__ = [
    "ApiKeyCreate",
    "ApiKeyCreated",
    "ApiKeyRead",
    "Page",
    "PageMeta",
    "ProblemDetail",
    "ProjectCreate",
    "ProjectRead",
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
