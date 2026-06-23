"""Shared pytest fixtures.

A single Postgres container is started for the whole session (the schema uses
JSONB/ARRAY, so a real Postgres is required). Each test starts from truncated
tables for isolation. The FastAPI app runs in-process via ``httpx.ASGITransport``.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session", autouse=True)
def _postgres() -> Iterator[None]:
    """Start a Postgres container and point app settings at it for the session."""
    with PostgresContainer(
        "postgres:16", username="fp", password="fp", dbname="floating_prompts_test"
    ) as container:
        os.environ.update(
            {
                "FP_ENVIRONMENT": "test",
                "FP_DB__HOST": container.get_container_host_ip(),
                "FP_DB__PORT": str(container.get_exposed_port(5432)),
                "FP_DB__USER": "fp",
                "FP_DB__PASSWORD": "fp",
                "FP_DB__NAME": "floating_prompts_test",
                "FP_LOG__JSON_LOGS": "false",
            }
        )

        # Reset cached settings/engine so they pick up the container.
        from floating_prompts.core.config import get_settings

        get_settings.cache_clear()
        settings = get_settings()

        # Create the schema with a throwaway sync engine.
        from floating_prompts.models import Base

        sync_engine = create_engine(settings.db.sync_url)
        Base.metadata.create_all(sync_engine)
        sync_engine.dispose()

        yield


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables() -> AsyncIterator[None]:
    """Truncate all tables before each test, and dispose the engine after.

    Each test runs on its own event loop, so the process-wide async engine is
    recreated per test (here) and disposed at teardown to avoid reusing pooled
    connections bound to a closed loop.
    """
    from floating_prompts.db.session import dispose_engine, get_engine
    from floating_prompts.models import Base

    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield
    await dispose_engine()


@pytest_asyncio.fixture
async def session() -> AsyncIterator[object]:
    """A transactional async session for direct service/repository tests."""
    from floating_prompts.db.session import session_scope

    async with session_scope() as s:
        yield s


@pytest.fixture
def app() -> object:
    """A fresh FastAPI application bound to the test settings."""
    from floating_prompts.api.app import create_app
    from floating_prompts.core.config import get_settings

    return create_app(get_settings())


@pytest_asyncio.fixture
async def admin_key() -> str:
    """Seed an admin API key and return its plaintext."""
    from floating_prompts.db.session import session_scope
    from floating_prompts.models.api_key import Scope
    from floating_prompts.services.api_key_service import ApiKeyService

    async with session_scope() as s:
        issued = await ApiKeyService(s).issue(
            name="test-admin",
            scopes=[Scope.ADMIN.value],
            project_slug=None,
            expires_at=None,
            actor="tests",
        )
        return issued.plaintext


@pytest_asyncio.fixture
async def client(app: object, admin_key: str) -> AsyncIterator[AsyncClient]:
    """Authenticated (admin) HTTP client against the in-process app."""
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"X-API-Key": admin_key},
    ) as c:
        yield c


@pytest_asyncio.fixture
async def anon_client(app: object) -> AsyncIterator[AsyncClient]:
    """Unauthenticated HTTP client."""
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
