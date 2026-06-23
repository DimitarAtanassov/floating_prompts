"""End-to-end tests through the HTTP API."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.e2e


async def _create_project(client: AsyncClient, slug: str = "acme") -> None:
    resp = await client.post(
        "/api/v1/projects", json={"slug": slug, "name": slug.title()}
    )
    assert resp.status_code == 201


async def test_health_is_public(anon_client: AsyncClient) -> None:
    resp = await anon_client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_unauthenticated_returns_problem_json(
    anon_client: AsyncClient,
) -> None:
    resp = await anon_client.get("/api/v1/projects")
    assert resp.status_code == 401
    assert resp.headers["content-type"].startswith("application/problem+json")
    assert resp.json()["code"] == "unauthenticated"


async def test_full_prompt_lifecycle(client: AsyncClient) -> None:
    await _create_project(client)

    base = "/api/v1/projects/acme/prompts/summarizer"
    v1 = await client.post(
        f"{base}/versions",
        json={"user_prompt": "Summarize:\n\n{{ content }}"},
    )
    assert v1.status_code == 201
    assert v1.json()["version"] == 1
    assert [s["name"] for s in v1.json()["variables"]] == ["content"]

    v2 = await client.post(
        f"{base}/versions", json={"user_prompt": "TL;DR:\n\n{{ content }}"}
    )
    assert v2.json()["version"] == 2

    tag = await client.put(f"{base}/tags/production", json={"version": 1})
    assert tag.status_code == 200

    resolved = await client.get(f"{base}/resolve", params={"tag": "production"})
    assert resolved.json()["version"] == 1

    rendered = await client.post(
        f"{base}/render", json={"variables": {"content": "Hello"}, "tag": "production"}
    )
    assert rendered.status_code == 200
    assert rendered.json()["user_prompt"] == "Summarize:\n\nHello"


async def test_render_missing_variable_is_422(client: AsyncClient) -> None:
    await _create_project(client)
    base = "/api/v1/projects/acme/prompts/greeter"
    await client.post(f"{base}/versions", json={"user_prompt": "Hi {{ name }}"})

    resp = await client.post(f"{base}/render", json={"variables": {}})
    assert resp.status_code == 422
    body = resp.json()
    assert body["code"] == "missing_variables"
    assert body["extra"]["missing"] == ["name"]


async def test_duplicate_project_is_409(client: AsyncClient) -> None:
    await _create_project(client)
    resp = await client.post("/api/v1/projects", json={"slug": "acme", "name": "Dup"})
    assert resp.status_code == 409
    assert resp.json()["code"] == "conflict"


async def test_insufficient_scope_is_forbidden(
    client: AsyncClient, app: object
) -> None:
    # Admin issues a read-only key.
    issued = await client.post(
        "/api/v1/api-keys", json={"name": "reader", "scopes": ["read"]}
    )
    assert issued.status_code == 201
    read_key = issued.json()["key"]

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(
        transport=transport, base_url="http://test", headers={"X-API-Key": read_key}
    ) as reader:
        # Reads are allowed.
        assert (await reader.get("/api/v1/projects")).status_code == 200
        # Writes are not.
        resp = await reader.post(
            "/api/v1/projects", json={"slug": "nope", "name": "Nope"}
        )
        assert resp.status_code == 403
        assert resp.json()["code"] == "forbidden"


async def test_invalid_slug_is_request_validation_error(
    client: AsyncClient,
) -> None:
    resp = await client.post(
        "/api/v1/projects", json={"slug": "Invalid Slug!", "name": "x"}
    )
    assert resp.status_code == 422
    assert resp.json()["code"] == "request_validation_error"
