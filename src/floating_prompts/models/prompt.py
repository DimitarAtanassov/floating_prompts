"""
Prompt model - simple versioned prompt storage.

Design: One table, minimal columns, maximum utility.
"""

from sqlalchemy import Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from floating_prompts.models.base import Base

__all__ = ["Prompt"]


class Prompt(Base):
    """
    A versioned prompt with system and user components.

    Simple design:
    - name: identifies the prompt (e.g., "paper_summary", "note_analysis")
    - version: allows multiple versions of the same prompt
    - system_prompt: optional system context
    - user_prompt: the main prompt template with {placeholders}

    Example:
        prompt = Prompt(
            name="summarizer",
            version=1,
            system_prompt="You are a helpful assistant.",
            user_prompt="Summarize this: {content}",
        )
    """

    __tablename__ = "prompts"

    # Identity - what prompt is this?
    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
        comment="Prompt identifier (e.g., 'paper_summary')",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Version number for this prompt",
    )

    # Content - the actual prompts
    system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="System prompt (optional)",
    )
    user_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User prompt template with {placeholders}",
    )

    # Unique constraint: only one prompt per (name, version) pair
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_prompt_name_version"),
    )

    def __repr__(self) -> str:
        return f"<Prompt(name='{self.name}', version={self.version})>"

    def render(self, **variables: str) -> tuple[str | None, str]:
        """
        Render the prompt with variable substitution.

        Args:
            **variables: Key-value pairs to substitute into the prompt.

        Returns:
            Tuple of (system_prompt, rendered_user_prompt).

        Example:
            system, user = prompt.render(content="Hello world")
        """
        rendered_user = self.user_prompt.format(**variables)
        return self.system_prompt, rendered_user
