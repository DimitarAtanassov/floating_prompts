"""floating_prompts - Database models for modelo services."""

from floating_prompts.config import DatabaseSettings, get_settings
from floating_prompts.models import (
    Base,
    LLMConfig,
    LLMModel,
    LLMProvider,
    Prompt,
    PromptConfig,
    PromptResponse,
    PromptTag,
    PromptTemplate,
)

__all__ = [
    # Config
    "get_settings",
    "DatabaseSettings",
    # Models
    "Base",
    "LLMProvider",
    "LLMModel",
    "LLMConfig",
    "PromptTemplate",
    "PromptConfig",
    "Prompt",
    "PromptResponse",
    "PromptTag",
]

__version__ = "0.1.0"
