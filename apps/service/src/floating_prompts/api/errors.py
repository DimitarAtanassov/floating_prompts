"""Exception handling — maps domain and framework errors to RFC 9457 problems.

Every error response uses ``application/problem+json`` with a
:class:`~floating_prompts_sdk.schemas.common.ProblemDetail` body, so clients get a
consistent, machine-readable shape and internals never leak.
"""

from __future__ import annotations

import orjson
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError

from floating_prompts.core.exceptions import DomainError
from floating_prompts.core.logging import get_logger
from floating_prompts_sdk.schemas.common import ProblemDetail

__all__ = ["register_exception_handlers"]

_PROBLEM_MEDIA_TYPE = "application/problem+json"
_logger = get_logger("floating_prompts.api")


def _problem_response(problem: ProblemDetail) -> Response:
    return Response(
        status_code=problem.status,
        content=orjson.dumps(problem.model_dump()),
        media_type=_PROBLEM_MEDIA_TYPE,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Install handlers for domain, validation, and unexpected errors."""

    @app.exception_handler(DomainError)
    async def _handle_domain(_: Request, exc: DomainError) -> Response:
        return _problem_response(
            ProblemDetail(
                title=exc.code.replace("_", " ").title(),
                status=exc.status_code,
                detail=exc.message,
                code=exc.code,
                extra=exc.extra,
            )
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(_: Request, exc: RequestValidationError) -> Response:
        return _problem_response(
            ProblemDetail(
                title="Request Validation Failed",
                status=422,
                detail="The request body or parameters are invalid.",
                code="request_validation_error",
                extra={"errors": exc.errors()},
            )
        )

    @app.exception_handler(Exception)
    async def _handle_unexpected(_: Request, exc: Exception) -> Response:
        _logger.error("unhandled_exception", error=str(exc), exc_info=exc)
        return _problem_response(
            ProblemDetail(
                title="Internal Server Error",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred.",
                code="internal_error",
            )
        )
