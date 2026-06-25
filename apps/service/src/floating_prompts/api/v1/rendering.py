"""Prompt rendering endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from floating_prompts.api.deps import PromptServiceDep
from floating_prompts_sdk.schemas.prompt import RenderRequest, RenderResult

__all__ = ["router"]

router = APIRouter(prefix="/projects/{slug}/prompts", tags=["rendering"])


@router.post("/{name}/render", summary="Render a prompt with variable values")
async def render_prompt(
    slug: str, name: str, payload: RenderRequest, service: PromptServiceDep
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
