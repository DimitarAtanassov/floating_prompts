"""Aggregate router for API v1."""

from __future__ import annotations

from fastapi import APIRouter

from floating_prompts.api.v1 import api_keys, health, projects, prompts, rendering

__all__ = ["api_router"]

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(projects.router)
api_router.include_router(prompts.router)
api_router.include_router(rendering.router)
api_router.include_router(api_keys.router)

# Health probes live at the root, outside the versioned prefix.
health_router = health.router
