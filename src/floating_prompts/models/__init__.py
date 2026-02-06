"""
Database models for floating_prompts.

Simple design: just one table for versioned prompts.
"""

from floating_prompts.models.base import Base
from floating_prompts.models.prompt import Prompt

__all__ = [
    "Base",
    "Prompt",
]
