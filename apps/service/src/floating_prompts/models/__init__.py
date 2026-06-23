"""SQLAlchemy ORM models.

Importing this package registers every model on ``Base.metadata`` so that
Alembic autogenerate and ``create_all`` see the full schema.
"""

from floating_prompts.db.base import Base
from floating_prompts.models.api_key import ApiKey, Scope
from floating_prompts.models.audit import AuditLog
from floating_prompts.models.project import Project
from floating_prompts.models.prompt import Prompt, PromptVersion, Tag

__all__ = [
    "ApiKey",
    "AuditLog",
    "Base",
    "Project",
    "Prompt",
    "PromptVersion",
    "Scope",
    "Tag",
]
