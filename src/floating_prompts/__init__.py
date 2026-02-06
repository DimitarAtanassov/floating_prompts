"""
floating_prompts - Simple versioned prompt storage.

Quick Start:
    from floating_prompts import Prompt, PromptRepository, get_session, init_db

    # Initialize database (creates tables if needed)
    init_db()

    # Create and query prompts
    with get_session() as session:
        repo = PromptRepository(session)
        
        # Create a prompt
        prompt = repo.create(
            name="summarizer",
            user_prompt="Summarize this: {content}",
            system_prompt="You are helpful.",
        )
        
        # Get latest version
        prompt = repo.get_by_name("summarizer")
        
        # Render with variables
        system, user = prompt.render(content="Hello world")
"""

from floating_prompts.config import DatabaseSettings, get_settings
from floating_prompts.database import get_session, init_db
from floating_prompts.models import Base, Prompt
from floating_prompts.repository import PromptRepository

__all__ = [
    # Config
    "get_settings",
    "DatabaseSettings",
    # Database
    "get_session",
    "init_db",
    # Models
    "Base",
    "Prompt",
    # Repository
    "PromptRepository",
]

__version__ = "0.1.0"
