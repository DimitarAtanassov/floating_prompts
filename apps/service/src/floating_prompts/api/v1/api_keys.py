"""API key management endpoints (admin scope required).

The first key must be created out-of-band via the ``floating-prompts bootstrap``
CLI command, since issuing keys over HTTP itself requires an admin key.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from floating_prompts.api.deps import ApiKeyServiceDep, AuthContext, require_scope
from floating_prompts.models.api_key import Scope
from floating_prompts_sdk.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyCreated,
    ApiKeyRead,
)

__all__ = ["router"]

router = APIRouter(tags=["api-keys"])

AdminAuth = Annotated[AuthContext, Depends(require_scope(Scope.ADMIN))]


@router.post(
    "/api-keys",
    status_code=status.HTTP_201_CREATED,
    summary="Issue an API key (secret shown once)",
)
async def issue_api_key(
    payload: ApiKeyCreate, service: ApiKeyServiceDep, auth: AdminAuth
) -> ApiKeyCreated:
    issued = await service.issue(
        name=payload.name,
        scopes=[s.value for s in payload.scopes],
        project_slug=payload.project_slug,
        expires_at=payload.expires_at,
        actor=auth.actor,
    )
    return ApiKeyCreated(
        **ApiKeyRead.model_validate(issued.api_key).model_dump(),
        key=issued.plaintext,
    )


@router.get(
    "/projects/{slug}/api-keys",
    summary="List a project's API keys",
)
async def list_api_keys(
    slug: str, service: ApiKeyServiceDep, _: AdminAuth
) -> list[ApiKeyRead]:
    keys = await service.list_for_project(project_slug=slug)
    return [ApiKeyRead.model_validate(k) for k in keys]


@router.delete("/api-keys/{key_id}", summary="Revoke an API key")
async def revoke_api_key(
    key_id: int, service: ApiKeyServiceDep, auth: AdminAuth
) -> ApiKeyRead:
    api_key = await service.revoke(key_id=key_id, actor=auth.actor)
    return ApiKeyRead.model_validate(api_key)
