"""Liveness and readiness probes (unauthenticated)."""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from floating_prompts.api.deps import SessionDep

__all__ = ["router"]

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Liveness probe")
async def healthz() -> dict[str, str]:
    """Return OK if the process is running."""
    return {"status": "ok"}


@router.get("/readyz", summary="Readiness probe")
async def readyz(session: SessionDep, response: Response) -> dict[str, str]:
    """Return OK only if the database is reachable."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - a probe must report, never raise
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "database": "down"}
    return {"status": "ok", "database": "up"}
