"""API key model.

Only the public ``prefix`` and the ``token_hash`` are persisted; the plaintext
key is shown to the caller once at creation and never stored. See
:mod:`floating_prompts.core.security`.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from floating_prompts.db.base import Base, IdMixin, TimestampMixin
from floating_prompts_sdk.scopes import Scope

if TYPE_CHECKING:
    from floating_prompts.models.project import Project

# ``Scope`` is part of the API contract and is owned by the SDK; it is re-exported
# here so service code can keep importing it from the model it annotates.
__all__ = ["ApiKey", "Scope"]


class ApiKey(IdMixin, TimestampMixin, Base):
    """A credential scoped to a project (or global when ``project_id`` is null)."""

    __tablename__ = "api_keys"

    project_id: Mapped[int | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, default=None
    )
    name: Mapped[str] = mapped_column(String(255))
    prefix: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(64))
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    project: Mapped[Project | None] = relationship(back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<ApiKey prefix={self.prefix!r} name={self.name!r}>"
