"""Unit tests for the SDK client using httpx's MockTransport (no server)."""

from __future__ import annotations

import httpx
import pytest

from floating_prompts_sdk import PromptsClient, PromptsClientError

pytestmark = pytest.mark.unit


def _client(handler: httpx.MockTransport) -> PromptsClient:
    return PromptsClient(
        "http://test",
        client=httpx.Client(base_url="http://test", transport=handler),
    )


def test_create_project_builds_request_and_parses_response() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/v1/projects"
        return httpx.Response(
            201,
            json={
                "id": 1,
                "slug": "acme",
                "name": "ACME",
                "description": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
        )

    with _client(httpx.MockTransport(handler)) as client:
        project = client.create_project("acme", "ACME")
    assert project.slug == "acme"


def test_error_response_is_raised_as_client_error() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            409,
            json={
                "title": "Conflict",
                "status": 409,
                "detail": "Project 'acme' already exists.",
                "code": "conflict",
                "extra": {"slug": "acme"},
            },
            headers={"content-type": "application/problem+json"},
        )

    with _client(httpx.MockTransport(handler)) as client:
        with pytest.raises(PromptsClientError) as exc:
            client.create_project("acme", "ACME")
    assert exc.value.status == 409
    assert exc.value.code == "conflict"
    assert exc.value.extra["slug"] == "acme"


def test_render_sends_variables_and_resolver() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "name": "greeter",
                "version": 2,
                "system_prompt": None,
                "user_prompt": "Hi Ada",
            },
        )

    with _client(httpx.MockTransport(handler)) as client:
        result = client.render("acme", "greeter", {"name": "Ada"}, tag="production")

    assert captured == {
        "variables": {"name": "Ada"},
        "version": None,
        "tag": "production",
    }
    assert result.user_prompt == "Hi Ada"
