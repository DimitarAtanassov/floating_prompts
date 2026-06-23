"""HTTP middleware: per-request correlation id and structured access logs."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from floating_prompts.core.logging import get_logger

__all__ = ["RequestContextMiddleware"]

_REQUEST_ID_HEADER = "X-Request-ID"
_logger = get_logger("floating_prompts.access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind a request id to the logging context and emit one access log line."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = request.headers.get(_REQUEST_ID_HEADER) or uuid.uuid4().hex
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            _logger.info(
                "request",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
            )
            structlog.contextvars.clear_contextvars()
        response.headers[_REQUEST_ID_HEADER] = request_id
        return response
