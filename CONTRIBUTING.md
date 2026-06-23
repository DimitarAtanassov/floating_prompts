# Contributing

Thanks for contributing to Floating Prompts! This guide gets you productive fast.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python toolchain + package manager)
- Docker (for Postgres and the test suite's `testcontainers`)

## Setup

```bash
uv sync                                              # install the whole workspace
uv run pre-commit install                            # enable git hooks (ruff, mypy, hygiene)
cp .env.example .env                                 # configure local settings
docker compose up -d postgres                        # start Postgres
uv run --directory apps/service alembic upgrade head # apply migrations
```

## Workspace layout

A [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) with two members:

```
apps/service/      floating-prompts-service  (import: floating_prompts)      the deployable app
packages/sdk/      floating-prompts-sdk      (import: floating_prompts_sdk)  SDK + API contract
```

The dependency DAG is `service → sdk` (never the reverse). The SDK owns the API
contract (Pydantic schemas + the `Scope` enum); the service imports it from there.

Within the **service**, layers depend **inward** only:

```
api/         HTTP layer (FastAPI routers, DI, error mapping)   ─┐ depends on
services/    business logic, transactions, audit               │ services
repositories/ async data access (no business rules)            │ → repositories
models/      SQLAlchemy ORM                                     │ → models
db/  core/   infrastructure (sessions, config, logging, errors) ┘
cli/         Typer CLI (uses the SDK)
```

When adding a feature, put behaviour at the right layer: persistence in a
repository, rules in a service, transport in a router; shared request/response
shapes go in the SDK's `schemas`.

## Quality gates

Run from the repo root (CI enforces all of these):

```bash
uv run ruff check apps packages                      # lint
uv run ruff format --check apps packages             # format
uv run mypy apps/service/src packages/sdk/src        # types (strict)
uv run pytest --cov                                  # tests + coverage >= 80%
```

## Database migrations

After changing a model under `apps/service/src/floating_prompts/models/`:

```bash
cd apps/service
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
```

Review the generated migration before committing. Autogenerate is a starting
point, not a guarantee.

## Tests

- `packages/sdk/tests`: SDK unit tests (schemas, client via `httpx.MockTransport`).
- `apps/service/tests/unit`: pure, fast, no I/O (rendering, security).
- `apps/service/tests/integration`: service + DB via a real Postgres container.
- `apps/service/tests/e2e`: full HTTP flows through the app.

Run a subset by marker: `uv run pytest -m unit`.
