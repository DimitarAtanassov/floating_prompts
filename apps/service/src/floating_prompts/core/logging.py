"""Structured logging via structlog.

``configure_logging`` wires structlog and the stdlib ``logging`` module to emit
either JSON (production) or a colourised console renderer (local dev). A
``request_id`` is bound per request by the API middleware and is automatically
included on every log line via the context-vars processor.
"""

from __future__ import annotations

import logging

import structlog

from floating_prompts.core.config import LoggingSettings

__all__ = ["configure_logging", "get_logger"]


def configure_logging(settings: LoggingSettings) -> None:
    """Configure structlog and the stdlib logging bridge.

    Idempotent: safe to call once at application startup.
    """
    level = logging.getLevelNamesMapping().get(settings.level.upper(), logging.INFO)

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]

    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer()
        if settings.json_logs
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, sqlalchemy, etc.) through the same level.
    logging.basicConfig(level=level, format="%(message)s")


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound structlog logger."""
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
