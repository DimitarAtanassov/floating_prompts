"""Async and sync HTTP clients for the Floating Prompts API.

The two clients expose the same surface; they differ only in ``await``. Shared
concerns — URL building and error mapping — live in module-level helpers so the
two implementations stay in lock-step (DRY).
"""

from __future__ import annotations

from types import TracebackType
from typing import Any, Self

import httpx

from floating_prompts_sdk.schemas.common import Page
from floating_prompts_sdk.schemas.project import ProjectRead
from floating_prompts_sdk.schemas.prompt import (
    PromptRead,
    PromptVersionRead,
    RenderResult,
    TagRead,
    VariableSpec,
)

__all__ = ["AsyncPromptsClient", "PromptsClient", "PromptsClientError"]


class PromptsClientError(Exception):
    """Raised when the API returns an error (parsed from problem+json)."""

    def __init__(
        self,
        message: str,
        *,
        status: int,
        code: str,
        extra: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.extra = extra or {}


def _check(response: httpx.Response) -> httpx.Response:
    """Raise :class:`PromptsClientError` for any 4xx/5xx response."""
    if response.is_success:
        return response
    try:
        problem = response.json()
    except ValueError:
        problem = {}
    raise PromptsClientError(
        problem.get("detail") or response.reason_phrase,
        status=response.status_code,
        code=problem.get("code", "http_error"),
        extra=problem.get("extra", {}),
    )


def _version_payload(
    user_prompt: str,
    system_prompt: str | None,
    variables: list[VariableSpec] | list[dict[str, Any]] | None,
) -> dict[str, Any]:
    specs: list[dict[str, Any]] | None = None
    if variables is not None:
        specs = [
            v.model_dump() if isinstance(v, VariableSpec) else v for v in variables
        ]
    return {
        "user_prompt": user_prompt,
        "system_prompt": system_prompt,
        "variables": specs,
    }


def _render_payload(
    variables: dict[str, Any], version: int | None, tag: str | None
) -> dict[str, Any]:
    return {"variables": variables, "version": version, "tag": tag}


class AsyncPromptsClient:
    """Async client for the Floating Prompts API."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        return _check(await self._client.request(method, path, **kwargs))

    # -- Health --------------------------------------------------------------

    async def health(self) -> dict[str, str]:
        data: dict[str, str] = (await self._request("GET", "/healthz")).json()
        return data

    # -- Projects ------------------------------------------------------------

    async def create_project(
        self, slug: str, name: str, description: str | None = None
    ) -> ProjectRead:
        resp = await self._request(
            "POST",
            "/api/v1/projects",
            json={"slug": slug, "name": name, "description": description},
        )
        return ProjectRead.model_validate(resp.json())

    async def list_projects(
        self, *, limit: int = 50, offset: int = 0
    ) -> Page[ProjectRead]:
        resp = await self._request(
            "GET", "/api/v1/projects", params={"limit": limit, "offset": offset}
        )
        return Page[ProjectRead].model_validate(resp.json())

    async def get_project(self, slug: str) -> ProjectRead:
        resp = await self._request("GET", f"/api/v1/projects/{slug}")
        return ProjectRead.model_validate(resp.json())

    async def delete_project(self, slug: str) -> None:
        await self._request("DELETE", f"/api/v1/projects/{slug}")

    # -- Prompts & versions --------------------------------------------------

    async def create_prompt(
        self, project: str, name: str, description: str | None = None
    ) -> PromptRead:
        resp = await self._request(
            "POST",
            f"/api/v1/projects/{project}/prompts",
            json={"name": name, "description": description},
        )
        return PromptRead.model_validate(resp.json())

    async def create_version(
        self,
        project: str,
        name: str,
        user_prompt: str,
        *,
        system_prompt: str | None = None,
        variables: list[VariableSpec] | list[dict[str, Any]] | None = None,
    ) -> PromptVersionRead:
        resp = await self._request(
            "POST",
            f"/api/v1/projects/{project}/prompts/{name}/versions",
            json=_version_payload(user_prompt, system_prompt, variables),
        )
        return PromptVersionRead.model_validate(resp.json())

    async def list_versions(self, project: str, name: str) -> list[PromptVersionRead]:
        resp = await self._request(
            "GET", f"/api/v1/projects/{project}/prompts/{name}/versions"
        )
        return [PromptVersionRead.model_validate(v) for v in resp.json()]

    async def resolve(
        self,
        project: str,
        name: str,
        *,
        version: int | None = None,
        tag: str | None = None,
    ) -> PromptVersionRead:
        params = {k: v for k, v in {"version": version, "tag": tag}.items() if v}
        resp = await self._request(
            "GET",
            f"/api/v1/projects/{project}/prompts/{name}/resolve",
            params=params,
        )
        return PromptVersionRead.model_validate(resp.json())

    # -- Tags ----------------------------------------------------------------

    async def set_tag(self, project: str, name: str, tag: str, version: int) -> TagRead:
        resp = await self._request(
            "PUT",
            f"/api/v1/projects/{project}/prompts/{name}/tags/{tag}",
            json={"version": version},
        )
        return TagRead.model_validate(resp.json())

    async def list_tags(self, project: str, name: str) -> list[TagRead]:
        resp = await self._request(
            "GET", f"/api/v1/projects/{project}/prompts/{name}/tags"
        )
        return [TagRead.model_validate(t) for t in resp.json()]

    async def delete_tag(self, project: str, name: str, tag: str) -> None:
        await self._request(
            "DELETE", f"/api/v1/projects/{project}/prompts/{name}/tags/{tag}"
        )

    # -- Rendering -----------------------------------------------------------

    async def render(
        self,
        project: str,
        name: str,
        variables: dict[str, Any],
        *,
        version: int | None = None,
        tag: str | None = None,
    ) -> RenderResult:
        resp = await self._request(
            "POST",
            f"/api/v1/projects/{project}/prompts/{name}/render",
            json=_render_payload(variables, version, tag),
        )
        return RenderResult.model_validate(resp.json())


class PromptsClient:
    """Synchronous client for the Floating Prompts API."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self._client = client or httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        return _check(self._client.request(method, path, **kwargs))

    def health(self) -> dict[str, str]:
        data: dict[str, str] = self._request("GET", "/healthz").json()
        return data

    def create_project(
        self, slug: str, name: str, description: str | None = None
    ) -> ProjectRead:
        resp = self._request(
            "POST",
            "/api/v1/projects",
            json={"slug": slug, "name": name, "description": description},
        )
        return ProjectRead.model_validate(resp.json())

    def list_projects(self, *, limit: int = 50, offset: int = 0) -> Page[ProjectRead]:
        resp = self._request(
            "GET", "/api/v1/projects", params={"limit": limit, "offset": offset}
        )
        return Page[ProjectRead].model_validate(resp.json())

    def get_project(self, slug: str) -> ProjectRead:
        resp = self._request("GET", f"/api/v1/projects/{slug}")
        return ProjectRead.model_validate(resp.json())

    def delete_project(self, slug: str) -> None:
        self._request("DELETE", f"/api/v1/projects/{slug}")

    def create_prompt(
        self, project: str, name: str, description: str | None = None
    ) -> PromptRead:
        resp = self._request(
            "POST",
            f"/api/v1/projects/{project}/prompts",
            json={"name": name, "description": description},
        )
        return PromptRead.model_validate(resp.json())

    def create_version(
        self,
        project: str,
        name: str,
        user_prompt: str,
        *,
        system_prompt: str | None = None,
        variables: list[VariableSpec] | list[dict[str, Any]] | None = None,
    ) -> PromptVersionRead:
        resp = self._request(
            "POST",
            f"/api/v1/projects/{project}/prompts/{name}/versions",
            json=_version_payload(user_prompt, system_prompt, variables),
        )
        return PromptVersionRead.model_validate(resp.json())

    def list_versions(self, project: str, name: str) -> list[PromptVersionRead]:
        resp = self._request(
            "GET", f"/api/v1/projects/{project}/prompts/{name}/versions"
        )
        return [PromptVersionRead.model_validate(v) for v in resp.json()]

    def resolve(
        self,
        project: str,
        name: str,
        *,
        version: int | None = None,
        tag: str | None = None,
    ) -> PromptVersionRead:
        params = {k: v for k, v in {"version": version, "tag": tag}.items() if v}
        resp = self._request(
            "GET",
            f"/api/v1/projects/{project}/prompts/{name}/resolve",
            params=params,
        )
        return PromptVersionRead.model_validate(resp.json())

    def set_tag(self, project: str, name: str, tag: str, version: int) -> TagRead:
        resp = self._request(
            "PUT",
            f"/api/v1/projects/{project}/prompts/{name}/tags/{tag}",
            json={"version": version},
        )
        return TagRead.model_validate(resp.json())

    def list_tags(self, project: str, name: str) -> list[TagRead]:
        resp = self._request("GET", f"/api/v1/projects/{project}/prompts/{name}/tags")
        return [TagRead.model_validate(t) for t in resp.json()]

    def delete_tag(self, project: str, name: str, tag: str) -> None:
        self._request("DELETE", f"/api/v1/projects/{project}/prompts/{name}/tags/{tag}")

    def render(
        self,
        project: str,
        name: str,
        variables: dict[str, Any],
        *,
        version: int | None = None,
        tag: str | None = None,
    ) -> RenderResult:
        resp = self._request(
            "POST",
            f"/api/v1/projects/{project}/prompts/{name}/render",
            json=_render_payload(variables, version, tag),
        )
        return RenderResult.model_validate(resp.json())
