"""
Prompt repository - simple CRUD operations.

Provides a clean interface for working with prompts without
exposing SQLAlchemy details to the rest of the application.
"""

from sqlalchemy import delete as sql_delete
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from floating_prompts.models import Prompt


class PromptRepository:
    """
    Repository for Prompt CRUD operations.

    Usage:
        with get_session() as session:
            repo = PromptRepository(session)
            
            # Create
            prompt = repo.create("summarizer", "Summarize: {content}")
            
            # Read
            prompt = repo.get_by_name("summarizer")  # Latest version
            prompt = repo.get_by_name("summarizer", version=2)
            
            # List
            all_prompts = repo.list_all()
            versions = repo.list_versions("summarizer")
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    # -------------------------------------------------------------------------
    # Create
    # -------------------------------------------------------------------------

    def create(
        self,
        name: str,
        user_prompt: str,
        system_prompt: str | None = None,
        version: int | None = None,
    ) -> Prompt:
        """
        Create a new prompt.

        If version is not specified, auto-increments from the latest version.

        Args:
            name: Prompt identifier.
            user_prompt: The user prompt template.
            system_prompt: Optional system prompt.
            version: Optional version number (auto-increments if not provided).

        Returns:
            The created Prompt instance.
        """
        if version is None:
            version = self._get_next_version(name)

        prompt = Prompt(
            name=name,
            version=version,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        self.session.add(prompt)
        self.session.flush()  # Get the ID without committing
        return prompt

    # -------------------------------------------------------------------------
    # Read
    # -------------------------------------------------------------------------

    def get_by_id(self, prompt_id: int) -> Prompt | None:
        """Get a prompt by its ID."""
        return self.session.get(Prompt, prompt_id)

    def get_by_name(self, name: str, version: int | None = None) -> Prompt | None:
        """
        Get a prompt by name and optionally version.

        If version is not specified, returns the latest version.

        Args:
            name: Prompt name.
            version: Specific version (optional, defaults to latest).

        Returns:
            Prompt if found, None otherwise.
        """
        query = select(Prompt).where(Prompt.name == name)

        if version is not None:
            query = query.where(Prompt.version == version)
        else:
            # Get latest version
            query = query.order_by(desc(Prompt.version))

        result = self.session.execute(query.limit(1))
        return result.scalar_one_or_none()

    def get_latest(self, name: str) -> Prompt | None:
        """Get the latest version of a prompt by name."""
        return self.get_by_name(name)

    # -------------------------------------------------------------------------
    # List
    # -------------------------------------------------------------------------

    def list_all(self) -> list[Prompt]:
        """List all prompts (all versions)."""
        query = select(Prompt).order_by(Prompt.name, desc(Prompt.version))
        result = self.session.execute(query)
        return list(result.scalars().all())

    def list_names(self) -> list[str]:
        """List unique prompt names."""
        query = select(Prompt.name).distinct().order_by(Prompt.name)
        result = self.session.execute(query)
        return list(result.scalars().all())

    def list_versions(self, name: str) -> list[Prompt]:
        """List all versions of a specific prompt."""
        query = (
            select(Prompt)
            .where(Prompt.name == name)
            .order_by(desc(Prompt.version))
        )
        result = self.session.execute(query)
        return list(result.scalars().all())

    def list_latest(self) -> list[Prompt]:
        """
        List only the latest version of each prompt.

        Returns one prompt per unique name.
        """
        # Subquery to get max version per name
        subquery = (
            select(Prompt.name, func.max(Prompt.version).label("max_version"))
            .group_by(Prompt.name)
            .subquery()
        )

        query = (
            select(Prompt)
            .join(
                subquery,
                (Prompt.name == subquery.c.name)
                & (Prompt.version == subquery.c.max_version),
            )
            .order_by(Prompt.name)
        )
        result = self.session.execute(query)
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Update
    # -------------------------------------------------------------------------

    def update(
        self,
        prompt: Prompt,
        user_prompt: str | None = None,
        system_prompt: str | None = None,
    ) -> Prompt:
        """
        Update an existing prompt.

        Note: Consider creating a new version instead of updating.

        Args:
            prompt: The prompt to update.
            user_prompt: New user prompt (optional).
            system_prompt: New system prompt (optional).

        Returns:
            The updated prompt.
        """
        if user_prompt is not None:
            prompt.user_prompt = user_prompt
        if system_prompt is not None:
            prompt.system_prompt = system_prompt
        self.session.flush()
        return prompt

    # -------------------------------------------------------------------------
    # Delete
    # -------------------------------------------------------------------------

    def delete(self, prompt: Prompt) -> None:
        """Delete a prompt."""
        self.session.delete(prompt)

    def delete_by_name(self, name: str, version: int | None = None) -> int:
        """
        Delete prompts by name.

        If version is specified, deletes only that version.
        Otherwise, deletes all versions.

        Returns:
            Number of prompts deleted.
        """
        query = sql_delete(Prompt).where(Prompt.name == name)
        if version is not None:
            query = query.where(Prompt.version == version)

        result = self.session.execute(query)
        return result.rowcount  # type: ignore[return-value]

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _get_next_version(self, name: str) -> int:
        """Get the next version number for a prompt name."""
        query = select(func.max(Prompt.version)).where(Prompt.name == name)
        result = self.session.execute(query)
        max_version = result.scalar()
        return (max_version or 0) + 1

    def exists(self, name: str, version: int | None = None) -> bool:
        """Check if a prompt exists."""
        return self.get_by_name(name, version) is not None
