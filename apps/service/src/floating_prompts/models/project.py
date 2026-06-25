"""Project model — the top-level namespace for prompts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from floating_prompts.db.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from floating_prompts.models.prompt import Prompt

__all__ = ["Project"]


class Project(IdMixin, TimestampMixin, Base):
    """A workspace that owns prompts.

    The ``slug`` is the stable, URL-safe identifier used in API paths
    (e.g. ``/api/v1/projects/{slug}/prompts``).
    """

    __tablename__ = "projects"

    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)

    prompts: Mapped[list[Prompt]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Project slug={self.slug!r}>"
