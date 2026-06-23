# 🎈 Floating Prompts

An async **prompt management service**: store prompts, version them immutably,
pin moving environment tags (`production`, `staging`), render them safely, and
gate access with scoped API keys.

- **FastAPI** service (async, Postgres) with OpenAPI docs at `/docs`
- **Typed Python SDK** + **CLI** for easy onboarding
- **Safe templating** (sandboxed Jinja2 with a declared-variable contract)
- **API-key auth** with `read` / `write` / `admin` scopes
- **Observability**: structured logs, `/healthz` · `/readyz` · `/metrics`, and an audit trail

> New here? Read the [docs](docs/README.md): a full deep dive and onboarding
> guide to the codebase (architecture, database schema, and API reference).

---

## Concepts

| Concept | What it is |
|---|---|
| **Project** | A namespace that owns prompts and API keys (`acme`). |
| **Prompt** | A named prompt within a project (`summarizer`). Identity only. |
| **Version** | An immutable revision of a prompt's content. Auto-incrementing. |
| **Tag** | A movable alias (`production`) pointing at a version. Pin this, not a number. |
| **API key** | A scoped credential. Shown once; only a hash is stored. |

Resolution precedence when reading a prompt: explicit **version** → **tag** → **latest**.

---

## Quick start (60 seconds)

```bash
uv sync                                      # 1. install the workspace
cp .env.example .env                         # 2. configure
docker compose up -d postgres                # 3. start Postgres
uv run --directory apps/service alembic upgrade head   # 4. create the schema
uv run floating-prompts serve                # 5. run the API  (http://localhost:8000/docs)
```

In another terminal, mint an admin key and drive the service from the CLI:

```bash
export FP_API_KEY=$(uv run floating-prompts bootstrap | tail -1)

uv run floating-prompts project create acme "ACME Corp"
uv run floating-prompts prompt add-version acme summarizer \
    "Summarize:\n\n{{ content }}" --system-prompt "You are concise."
uv run floating-prompts tag set acme summarizer production 1
uv run floating-prompts prompt render acme summarizer \
    --var content="Hello, world!" --tag production
```

> The whole stack (Postgres + migrated API) also runs with
> `docker compose --profile full up --build`.

---

## Using the SDK

```python
from floating_prompts_sdk import PromptsClient  # AsyncPromptsClient is also available

with PromptsClient("http://localhost:8000", api_key="fp_...") as client:
    client.create_project("acme", "ACME Corp")
    client.create_version(
        "acme", "summarizer",
        user_prompt="Summarize:\n\n{{ content }}",
        system_prompt="You are concise.",
    )
    client.set_tag("acme", "summarizer", "production", version=1)

    result = client.render("acme", "summarizer",
                           {"content": "Hello!"}, tag="production")
    print(result.user_prompt)  # -> "Summarize:\n\nHello!"
```

See [`examples/quickstart.py`](examples/quickstart.py) for a runnable version.

---

## API overview

All endpoints are under `/api/v1` and require an `X-API-Key` header. Errors use
RFC 9457 `application/problem+json`.

| Method & path | Scope | Description |
|---|---|---|
| `POST /projects` | write | Create a project |
| `GET /projects` · `GET /projects/{slug}` | read | List / get projects |
| `DELETE /projects/{slug}` | admin | Delete a project |
| `POST /projects/{slug}/prompts` | write | Create a prompt |
| `POST /projects/{slug}/prompts/{name}/versions` | write | Add a version |
| `GET /projects/{slug}/prompts/{name}/versions` | read | List versions |
| `GET /projects/{slug}/prompts/{name}/resolve?version=&tag=` | read | Resolve to a version |
| `PUT /projects/{slug}/prompts/{name}/tags/{tag}` | write | Create / move a tag |
| `POST /projects/{slug}/prompts/{name}/render` | read | Render with variables |
| `POST /api-keys` | admin | Issue a key (secret shown once) |
| `GET /healthz` · `/readyz` · `/metrics` | none | Probes & Prometheus metrics |

Interactive docs: **`/docs`** (Swagger) and **`/redoc`**.

---

## Templating

Templates use Jinja2 (`{{ variable }}`) rendered in a **sandbox** with strict
undefined handling. Each version declares its variables (inferred from the
template if you don't pass them). Rendering validates the supplied values:

- missing a required variable → `422 missing_variables`
- supplying an undeclared variable → `422 unknown_variables`
- attribute-escape / injection attempts → `422 template_error`

---

## Configuration

Settings come from environment variables (prefix `FP_`, nested with `__`) or
`.env`. See [`.env.example`](.env.example). Highlights:

| Variable | Default | Meaning |
|---|---|---|
| `FP_DB__HOST` / `__PORT` / `__USER` / `__PASSWORD` / `__NAME` | localhost / 5432 / postgres / postgres / floating_prompts | Postgres connection |
| `FP_SERVER__PORT` | 8000 | HTTP port |
| `FP_LOG__JSON_LOGS` | true | JSON logs (set `false` for pretty console) |
| `FP_ENVIRONMENT` | local | `local` / `test` / `staging` / `production` |

---

## Repository layout

A [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) with two members:

```
apps/service/        floating-prompts-service: the FastAPI app (import: floating_prompts) + migrations
packages/sdk/        floating-prompts-sdk:     the SDK + API contract (import: floating_prompts_sdk)
```

The service depends on the SDK for the API schemas (one source of truth); the
SDK is standalone (`pydantic` + `httpx` only). One `uv.lock`, one `uv sync`.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). Run the quality gates from the repo root:

```bash
uv run ruff check apps packages && uv run mypy apps/service/src packages/sdk/src && uv run pytest --cov
```

## License

MIT
