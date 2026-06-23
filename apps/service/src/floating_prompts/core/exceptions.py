"""Domain exception hierarchy.

These exceptions are raised by the service and repository layers and are
deliberately transport-agnostic — they carry an HTTP-ish ``status_code`` and a
machine-readable ``code`` so the API layer can map them to RFC 9457
``application/problem+json`` responses without leaking internals. Nothing here
imports FastAPI.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "DomainError",
    "NotFoundError",
    "ValidationError",
]


class DomainError(Exception):
    """Base class for all expected, business-level errors.

    Attributes:
        message: Human-readable description (becomes the problem ``detail``).
        status_code: HTTP status the API layer should respond with.
        code: Stable, machine-readable error identifier for clients.
        extra: Optional structured fields appended to the problem document.
    """

    status_code: int = 500
    code: str = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        self.extra: dict[str, Any] = extra or {}


class NotFoundError(DomainError):
    """A requested resource does not exist."""

    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    """The request conflicts with current state (e.g. duplicate slug)."""

    status_code = 409
    code = "conflict"


class ValidationError(DomainError):
    """The request is well-formed but semantically invalid.

    Used for domain rules that Pydantic cannot express, such as rendering a
    template with missing variables.
    """

    status_code = 422
    code = "validation_error"


class AuthenticationError(DomainError):
    """The caller could not be authenticated (missing/invalid API key)."""

    status_code = 401
    code = "unauthenticated"


class AuthorizationError(DomainError):
    """The caller is authenticated but lacks the required scope."""

    status_code = 403
    code = "forbidden"
