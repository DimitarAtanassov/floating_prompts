"""Async data-access layer.

Repositories translate between the ORM and the rest of the app. They contain
*no* business rules — only persistence and queries. Transactions (commit /
rollback) are owned by the caller (the service layer / session scope), so
repositories never commit on their own.
"""

from floating_prompts.repositories.base import AsyncRepository
from floating_prompts.repositories.project import ProjectRepository
from floating_prompts.repositories.prompt import PromptRepository

__all__ = [
    "AsyncRepository",
    "ProjectRepository",
    "PromptRepository",
]
