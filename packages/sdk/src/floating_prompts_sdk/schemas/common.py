"""Shared schema building blocks: pagination and error envelope."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

__all__ = ["Page", "PageMeta", "ProblemDetail"]


class PageMeta(BaseModel):
    """Pagination metadata."""

    total: int = Field(description="Total number of items available.")
    limit: int = Field(description="Maximum items per page.")
    offset: int = Field(description="Number of items skipped.")


class Page[ItemT](BaseModel):
    """A page of results plus its pagination metadata."""

    items: list[ItemT]
    meta: PageMeta

    @classmethod
    def of(
        cls, items: list[ItemT], *, total: int, limit: int, offset: int
    ) -> Page[ItemT]:
        """Build a page from items and pagination parameters."""
        return cls(items=items, meta=PageMeta(total=total, limit=limit, offset=offset))


class ProblemDetail(BaseModel):
    """RFC 9457 problem detail returned for all error responses."""

    type: str = Field(default="about:blank", description="Error type URI.")
    title: str = Field(description="Short, human-readable summary.")
    status: int = Field(description="HTTP status code.")
    detail: str | None = Field(default=None, description="Human-readable detail.")
    code: str = Field(description="Stable machine-readable error code.")
    extra: dict[str, Any] = Field(
        default_factory=dict, description="Additional structured context."
    )
