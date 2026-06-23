"""Prompt domain models.

The single-table design of the original library conflated three distinct
concerns. They are separated here:

* :class:`Prompt` — stable *identity* (a name within a project).
* :class:`PromptVersion` — *immutable content* for one revision.
* :class:`Tag` — a *mutable alias* (e.g. ``production``) pointing at a version,
  so consumers can pin a moving label instead of a hard version number.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from floating_prompts.db.base import Base, IdMixin, TimestampMixin

if TYPE_CHECKING:
    from floating_prompts.models.project import Project

__all__ = ["Prompt", "PromptVersion", "Tag"]


class Prompt(IdMixin, TimestampMixin, Base):
    """The identity of a prompt within a project. Holds no rendered content."""

    __tablename__ = "prompts"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_prompts_project_id_name"),
    )

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)

    project: Mapped[Project] = relationship(back_populates="prompts")
    versions: Mapped[list[PromptVersion]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="PromptVersion.version",
    )
    tags: Mapped[list[Tag]] = relationship(
        back_populates="prompt",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Prompt name={self.name!r} project_id={self.project_id}>"


class PromptVersion(IdMixin, TimestampMixin, Base):
    """An immutable revision of a prompt's content.

    ``variables`` is the declared variable contract for the template, stored as
    a list of ``{"name": str, "required": bool, "description": str | None}``
    objects and validated at render time.
    """

    __tablename__ = "prompt_versions"
    __table_args__ = (
        UniqueConstraint(
            "prompt_id", "version", name="uq_prompt_versions_prompt_id_version"
        ),
    )

    prompt_id: Mapped[int] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int] = mapped_column(Integer)
    system_prompt: Mapped[str | None] = mapped_column(Text, default=None)
    user_prompt: Mapped[str] = mapped_column(Text)
    variables: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    created_by: Mapped[str | None] = mapped_column(String(255), default=None)

    prompt: Mapped[Prompt] = relationship(back_populates="versions")

    def __repr__(self) -> str:
        return f"<PromptVersion prompt_id={self.prompt_id} v{self.version}>"


class Tag(IdMixin, TimestampMixin, Base):
    """A mutable, named pointer from a prompt to one of its versions."""

    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("prompt_id", "name", name="uq_tags_prompt_id_name"),
        Index("ix_tags_version_id", "version_id"),
    )

    prompt_id: Mapped[int] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"), index=True
    )
    version_id: Mapped[int] = mapped_column(
        ForeignKey("prompt_versions.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(64))

    prompt: Mapped[Prompt] = relationship(back_populates="tags")
    version: Mapped[PromptVersion] = relationship()

    def __repr__(self) -> str:
        return f"<Tag name={self.name!r} prompt_id={self.prompt_id}>"
