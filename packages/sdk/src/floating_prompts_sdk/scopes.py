"""API-key permission scopes.

Part of the API contract, so it lives in the SDK: clients reason about the
scopes they request, and the service imports the same enum for its ORM model
and authorization checks.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = ["Scope"]


class Scope(StrEnum):
    """Permissions an API key may be granted."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
