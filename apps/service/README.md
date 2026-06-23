# floating-prompts-service

The deployable [Floating Prompts](../../README.md) FastAPI application: versioned
prompt management with environment tags, sandboxed templating, scoped API-key
auth, and observability. Depends on
[`floating-prompts-sdk`](../../packages/sdk) for the API contract.

Run from the repo root:

```bash
docker compose up -d postgres
cd apps/service && uv run alembic upgrade head
uv run floating-prompts serve          # http://localhost:8000/docs
```

Import package: `floating_prompts` (`api/`, `services/`, `repositories/`,
`models/`, `db/`, `core/`, `cli/`). Migrations live in `alembic/`.

See the [root README](../../README.md) for the full quickstart, API reference,
and configuration.
