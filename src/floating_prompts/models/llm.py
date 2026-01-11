from __future__ import annotations

from typing import Any

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from floating_prompts.models.base import Base

__all__ = [
    "LLMProvider",
    "LLMModel",
    "LLMConfig",
]


# =============================================================================
# LLMProvider - The AI provider (OpenAI, Anthropic, etc.)
# =============================================================================


class LLMProvider(Base):
    """
    Stores LLM provider information.
    
    Represents companies/services that provide LLM APIs.
    """

    __tablename__ = "llm_providers"

    # Identity
    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True,
        comment="Provider name (e.g., 'openai', 'anthropic', 'google')",
    )

    # Relationships
    models: Mapped[list[LLMModel]] = relationship(
        "LLMModel",
        back_populates="provider",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<LLMProvider(name={self.name})>"


# =============================================================================
# LLMModel - Specific models from a provider
# =============================================================================


class LLMModel(Base):
    """
    Stores LLM model information.
    
    Represents specific models available from a provider.
    """

    __tablename__ = "llm_models"

    # Foreign key to provider (proper FK constraint)
    provider_id: Mapped[str] = mapped_column(
        ForeignKey("llm_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The provider this model belongs to",
    )

    # Identity
    api_model_name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
        comment="Model identifier (e.g., 'gpt-4', 'claude-3-opus-20240229')",
    )
    display_name: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable name (e.g., 'GPT-4', 'Claude 3 Opus')",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description of the model's capabilities",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this model is enabled for use",
    )
    is_deprecated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this model is deprecated",
    )
    deprecation_date: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Date when the model will be/was deprecated",
    )

    # Relationships
    provider: Mapped[LLMProvider] = relationship(
        "LLMProvider",
        back_populates="models",
    )
    configs: Mapped[list[LLMConfig]] = relationship(
        "LLMConfig",
        back_populates="model",
        cascade="all, delete-orphan",
    )

    # Constraints - REMOVE ix_model_provider (already created by index=True on provider_id)
    __table_args__ = (
        UniqueConstraint("provider_id", "api_model_name", name="uq_model_provider_name"),
        Index("ix_model_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<LLMModel(api_model_name={self.api_model_name})>"


# =============================================================================
# LLMConfig - Reusable LLM configuration presets
# =============================================================================


class LLMConfig(Base):
    """
    Stores reusable LLM configuration presets.
    
    Allows defining named configurations that can be referenced by prompts.
    """

    __tablename__ = "llm_configs"

    # Foreign key to model (proper FK constraint)
    model_id: Mapped[str] = mapped_column(
        ForeignKey("llm_models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="The model this config uses",
    )

    # Identity
    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True,
        comment="Unique name for this config (e.g., 'creative-writing', 'precise-extraction')",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Description of this configuration's purpose",
    )

    # LLM parameters
    temperature: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Temperature setting (0.0-2.0)",
    )

    # Additional settings (provider-specific)
    extra_settings: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional provider-specific settings: max_tokens, top_p, etc.",
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this config is enabled",
    )

    # Relationships
    model: Mapped[LLMModel] = relationship(
        "LLMModel",
        back_populates="configs",
    )

    def __repr__(self) -> str:
        return f"<LLMConfig(name={self.name})>"

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary for LLM API calls."""
        settings: dict[str, Any] = {}
        if self.temperature is not None:
            settings["temperature"] = self.temperature
        if self.extra_settings:
            settings.update(self.extra_settings)
        return settings
