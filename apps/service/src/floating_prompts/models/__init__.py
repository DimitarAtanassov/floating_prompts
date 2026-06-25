"""SQLAlchemy ORM models.

Importing this package registers every model on ``Base.metadata`` so that
Alembic autogenerate and ``create_all`` see the full schema.
"""

from floating_prompts.db.base import Base
from floating_prompts.models.project import Project
from floating_prompts.models.prompt import Prompt, PromptVersion, Tag

__all__ = [
    "Base",
    "Project",
    "Prompt",
    "PromptVersion",
    "Tag",
]
