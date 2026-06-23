"""Application factory.

``create_app`` assembles the FastAPI application: logging, middleware, metrics,
routers, exception handlers, and a lifespan that disposes the DB engine on
shutdown. Importing this module has no side effects, which keeps it friendly to
testing and to ``uvicorn --factory``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from floating_prompts import __version__
from floating_prompts.api.errors import register_exception_handlers
from floating_prompts.api.middleware import RequestContextMiddleware
from floating_prompts.api.v1.router import api_router, health_router
from floating_prompts.core.config import AppSettings, get_settings
from floating_prompts.core.logging import configure_logging, get_logger
from floating_prompts.db.session import dispose_engine

__all__ = ["create_app"]


def create_app(settings: AppSettings | None = None) -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = settings or get_settings()
    configure_logging(settings.log)
    logger = get_logger("floating_prompts.app")

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info("startup", environment=settings.environment, version=__version__)
        yield
        await dispose_engine()
        logger.info("shutdown")

    app = FastAPI(
        title="Floating Prompts",
        version=__version__,
        summary="Versioned prompt management with tags, safe templating, and API keys.",
        root_path=settings.server.root_path,
        lifespan=lifespan,
    )

    if settings.server.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.server.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(api_router)

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    return app
