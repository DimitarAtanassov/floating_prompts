"""Typer CLI.

Two kinds of commands:

* **Operator** commands (``serve``) run the service locally.
* **Client** commands (``project``, ``prompt``, ``tag``) talk to a running API
  via the SDK, reading ``--url`` (or ``FP_API_URL``).
"""

from __future__ import annotations

import json
from typing import Annotated, Any

import typer

from floating_prompts_sdk import PromptsClient, PromptsClientError

app = typer.Typer(
    name="floating-prompts",
    help="Manage versioned prompts: projects, versions, tags, and rendering.",
    no_args_is_help=True,
    add_completion=False,
)
project_app = typer.Typer(help="Manage projects.", no_args_is_help=True)
prompt_app = typer.Typer(help="Manage prompts and versions.", no_args_is_help=True)
tag_app = typer.Typer(help="Manage prompt tags.", no_args_is_help=True)
app.add_typer(project_app, name="project")
app.add_typer(prompt_app, name="prompt")
app.add_typer(tag_app, name="tag")

UrlOpt = Annotated[
    str, typer.Option("--url", envvar="FP_API_URL", help="API base URL.")
]


def _client(url: str) -> PromptsClient:
    return PromptsClient(url)


def _echo(model: Any) -> None:
    """Print a Pydantic model (or list of them) as indented JSON."""
    if isinstance(model, list):
        payload = [m.model_dump(mode="json") for m in model]
    else:
        payload = model.model_dump(mode="json")
    typer.echo(json.dumps(payload, indent=2))


def _run_client(fn: Any) -> None:
    """Execute an SDK call, turning API errors into clean CLI failures."""
    try:
        fn()
    except PromptsClientError as exc:
        typer.secho(f"error [{exc.code}]: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc


# -- Operator commands -------------------------------------------------------


@app.command()
def serve(
    host: Annotated[str | None, typer.Option(help="Bind host.")] = None,
    port: Annotated[int | None, typer.Option(help="Bind port.")] = None,
    reload: Annotated[bool, typer.Option(help="Auto-reload (dev).")] = False,
) -> None:
    """Run the HTTP API with uvicorn."""
    import uvicorn

    from floating_prompts.core.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "floating_prompts.api.app:create_app",
        factory=True,
        host=host or settings.server.host,
        port=port or settings.server.port,
        reload=reload,
    )


# -- Project commands --------------------------------------------------------


@project_app.command("create")
def project_create(
    slug: str,
    name: str,
    url: UrlOpt = "http://localhost:8000",
    description: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Create a project."""

    def _do() -> None:
        with _client(url) as client:
            _echo(client.create_project(slug, name, description))

    _run_client(_do)


@project_app.command("list")
def project_list(url: UrlOpt = "http://localhost:8000") -> None:
    """List projects."""

    def _do() -> None:
        with _client(url) as client:
            _echo(client.list_projects().items)

    _run_client(_do)


# -- Prompt commands ---------------------------------------------------------


@prompt_app.command("add-version")
def prompt_add_version(
    project: str,
    name: str,
    user_prompt: str,
    url: UrlOpt = "http://localhost:8000",
    system_prompt: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Create a new version of a prompt (auto-increments the version number)."""

    def _do() -> None:
        with _client(url) as client:
            _echo(
                client.create_version(
                    project, name, user_prompt, system_prompt=system_prompt
                )
            )

    _run_client(_do)


@prompt_app.command("versions")
def prompt_versions(
    project: str, name: str, url: UrlOpt = "http://localhost:8000"
) -> None:
    """List all versions of a prompt."""

    def _do() -> None:
        with _client(url) as client:
            _echo(client.list_versions(project, name))

    _run_client(_do)


@prompt_app.command("render")
def prompt_render(
    project: str,
    name: str,
    url: UrlOpt = "http://localhost:8000",
    var: Annotated[
        list[str] | None,
        typer.Option("--var", help="Variable as key=value (repeatable)."),
    ] = None,
    version: Annotated[int | None, typer.Option()] = None,
    tag: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Render a prompt with variable values."""
    values: dict[str, Any] = {}
    for item in var or []:
        key, _, value = item.partition("=")
        values[key] = value

    def _do() -> None:
        with _client(url) as client:
            _echo(client.render(project, name, values, version=version, tag=tag))

    _run_client(_do)


# -- Tag commands ------------------------------------------------------------


@tag_app.command("set")
def tag_set(
    project: str,
    name: str,
    tag: str,
    version: int,
    url: UrlOpt = "http://localhost:8000",
) -> None:
    """Point a tag at a specific version."""

    def _do() -> None:
        with _client(url) as client:
            _echo(client.set_tag(project, name, tag, version))

    _run_client(_do)


@tag_app.command("list")
def tag_list(project: str, name: str, url: UrlOpt = "http://localhost:8000") -> None:
    """List a prompt's tags."""

    def _do() -> None:
        with _client(url) as client:
            _echo(client.list_tags(project, name))

    _run_client(_do)


if __name__ == "__main__":
    app()
