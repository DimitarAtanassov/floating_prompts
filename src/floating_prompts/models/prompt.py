from __future__ import annotations

from typing import Any

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Table,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Column,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from floating_prompts.models.base import Base

from floating_prompts.models.llm import LLMConfig, LLMModel

__all__ = [
    "PromptTemplate",
    "PromptConfig",
    "Prompt",
    "PromptResponse",
    "PromptTag",
    "prompt_tag_associations",
]


# =============================================================================
# PromptTemplate - The actual prompt text content (versioned)
# =============================================================================


class PromptTemplate(Base):
    """
    Stores the actual prompt text content.
    
    This is the "source code" of your prompts - immutable once created.
    New versions create new rows, enabling full version history.    
    Design: Immutable append-only table (like git commits)
    """

    __tablename__ = "prompt_templates"

    # Identity
    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
        comment="Logical name grouping template versions (e.g., 'summarizer')",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sequential version number within this template name",
    )

    # Content - the actual prompt text
    system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="System prompt content",
    )
    user_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User prompt template with {placeholders}",
    )

    # Metadata
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="What this template does",
    )

    # Relationships
    configs: Mapped[list[PromptConfig]] = relationship(
        "PromptConfig",
        back_populates="template",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_template_name_version"),
    )

    def __repr__(self) -> str:
        return f"<PromptTemplate(name={self.name}, v={self.version})>"


# =============================================================================
# PromptConfig - How to use a template (schemas, defaults)
# =============================================================================


class PromptConfig(Base):
    """
    Configuration for using a template.    
    Separates WHAT the prompt says (template) from HOW it's used (config).
    Same template can have multiple configs for different use cases.
    """

    __tablename__ = "prompt_configs"

    # Foreign key to template
    template_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="The template this config uses",
    )

    # Identity
    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Descriptive name for this config",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Config version (configs can also evolve)",
    )

    # Input specification
    input_schema: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON Schema defining expected input variables and types",
    )

    # Output specification
    output_schema: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON Schema or Pydantic schema for structured outputs",
    )
    output_format: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Expected format: 'json', 'markdown', 'text', 'code', 'structured'",
    )

    # Relationships
    template: Mapped[PromptTemplate] = relationship(
        "PromptTemplate",
        back_populates="configs",
    )
    prompts: Mapped[list[Prompt]] = relationship(
        "Prompt",
        back_populates="config",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_config_name_version"),
    )

    def __repr__(self) -> str:
        return f"<PromptConfig(name={self.name}, v={self.version})>"


# =============================================================================
# Prompt - A fully rendered, executable prompt instance
# =============================================================================


class Prompt(Base):
    """
    A fully rendered prompt ready for execution.    
    Stores the complete rendered prompts (after variable substitution)
    along with all settings needed for execution.
    """

    __tablename__ = "prompts"

    # Foreign key to config
    config_id: Mapped[str] = mapped_column(
        ForeignKey("prompt_configs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="The config this prompt uses",
    )

    # Identity
    display_name: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable name for UI",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description of this prompt's purpose",
    )

    # Rendered prompts (the full loaded prompt)
    rendered_system_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Final system prompt after variable substitution",
    )
    rendered_user_prompt: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Final user prompt after variable substitution",
    )

    # Dynamic input values used for rendering
    input_values: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Input values used to render the prompt",
    )

    # Deployment
    environment: Mapped[str] = mapped_column(
        Text,
        default="development",
        nullable=False,
        comment="Target environment: 'development', 'staging', 'production'",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this prompt is enabled",
    )

    # Categorization
    category: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Category: 'summarization', 'extraction', 'generation', etc.",
    )

    # Relationships
    config: Mapped[PromptConfig] = relationship(
        "PromptConfig",
        back_populates="prompts",
    )
    responses: Mapped[list[PromptResponse]] = relationship(
        "PromptResponse",
        back_populates="prompt",
        cascade="all, delete-orphan",
    )
    tags: Mapped[list[PromptTag]] = relationship(
        "PromptTag",
        secondary="prompt_tag_associations",
        back_populates="prompts",
    )

    # Constraints
    __table_args__ = (
        Index("ix_prompt_environment", "environment"),
        Index("ix_prompt_category_active", "category", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Prompt(id={self.id}, env={self.environment})>"

    @property
    def template(self) -> PromptTemplate:
        """Convenience accessor for the underlying template."""
        return self.config.template


# =============================================================================
# PromptResponse - LLM responses to prompts
# =============================================================================


class PromptResponse(Base):
    """
    Stores LLM responses to prompts.
    Records the raw response, parsed output, and execution metrics.
    LLM configuration is captured via foreign keys.
    """

    __tablename__ = "prompt_responses"

    # Foreign key - links to the prompt
    prompt_id: Mapped[str] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The prompt that generated this response",
    )

    # Foreign key - which LLM config was used
    llm_config_id: Mapped[str | None] = mapped_column(
        ForeignKey("llm_configs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="The LLM config used for this response",
    )

    # Foreign key - which model was actually used
    llm_model_id: Mapped[str | None] = mapped_column(
        ForeignKey("llm_models.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="The LLM model that generated this response",
    )

    # Response content
    llm_response: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="LLM response: {'raw': 'text...', 'parsed': {...}}",
    )

    # Metrics
    input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of input tokens",
    )
    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Number of output tokens",
    )
    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Response latency in milliseconds",
    )

    # Status
    success: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
        comment="Whether the response was successful",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Error message if failed",
    )

    # Relationships
    prompt: Mapped[Prompt] = relationship(
        "Prompt",
        back_populates="responses",
    )
    llm_config: Mapped[LLMConfig | None] = relationship(
        "LLMConfig",
    )
    llm_model: Mapped[LLMModel | None] = relationship(
        "LLMModel",
    )

    # Constraints
    __table_args__ = (
        Index("ix_response_prompt_created", "prompt_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<PromptResponse(prompt_id={self.prompt_id}, success={self.success})>"


# =============================================================================
# Tags
# =============================================================================


# Association table (no class needed)
prompt_tag_associations = Table(
    "prompt_tag_associations",
    Base.metadata,
    Column("prompt_id", UUID(as_uuid=False), ForeignKey("prompts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=False), ForeignKey("prompt_tags.id", ondelete="CASCADE"), primary_key=True),
)


class PromptTag(Base):
    """Tags for categorizing prompts."""

    __tablename__ = "prompt_tags"

    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    prompts: Mapped[list[Prompt]] = relationship(
        "Prompt",
        secondary=prompt_tag_associations,
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<PromptTag(name={self.name})>"
