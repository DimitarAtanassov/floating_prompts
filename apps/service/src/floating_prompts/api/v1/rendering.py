"""Prompt rendering endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from floating_prompts.api.deps import AuthContext, PromptServiceDep, require_scope
from floating_prompts.models.api_key import Scope
from floating_prompts_sdk.schemas.prompt import RenderRequest, RenderResult

__all__ = ["router"]

router = APIRouter(prefix="/projects/{slug}/prompts", tags=["rendering"])

ReadAuth = Annotated[AuthContext, Depends(require_scope(Scope.READ))]


@router.post("/{name}/render", summary="Render a prompt with variable values")
async def render_prompt(
    slug: str,
    name: str,
    payload: RenderRequest,
    service: PromptServiceDep,
    _: ReadAuth,
) -> RenderResult:
    version, rendered = await service.render(
        project_slug=slug,
        name=name,
        values=payload.variables,
        version=payload.version,
        tag=payload.tag,
    )
    return RenderResult(
        name=name,
        version=version.version,
        system_prompt=rendered.system_prompt,
        user_prompt=rendered.user_prompt,
    )
