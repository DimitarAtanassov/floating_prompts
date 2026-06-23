# API Reference

HTTP API for the Floating Prompts service. Use this to explore the service by
hand (curl) or to understand the SDK.

Interactive docs are also served live at `/docs` (Swagger) and `/redoc`.

Related docs: [Architecture](ARCHITECTURE.md), [Database schema](DATABASE.md).

---

## Base URL and versioning

All business endpoints are under `/api/v1`. Health and metrics endpoints live at
the root. The default local base URL is `http://localhost:8000`.

## Authentication

Every `/api/v1` endpoint requires an API key in the `X-API-Key` header.

```
X-API-Key: fp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Keys carry scopes. Scope order is `read`, `write`, `admin`, and `admin` implies
the others.

| Missing or bad key | Wrong scope |
|---|---|
| `401 unauthenticated` | `403 forbidden` |

Create the first `admin` key out of band:

```bash
uv run floating-prompts bootstrap            # prints the key once
```

## Errors

All errors use `application/problem+json` (RFC 9457):

```json
{
  "type": "about:blank",
  "title": "Conflict",
  "status": 409,
  "detail": "Project 'acme' already exists.",
  "code": "conflict",
  "extra": { "slug": "acme" }
}
```

Branch on `code`. Common codes: `not_found`, `conflict`, `validation_error`,
`missing_variables`, `unknown_variables`, `template_error`, `unauthenticated`,
`forbidden`, `request_validation_error`.

---

## Endpoint summary

| Method | Path | Scope | Purpose |
|---|---|---|---|
| GET | `/healthz` | none | Liveness |
| GET | `/readyz` | none | Readiness (checks DB) |
| GET | `/metrics` | none | Prometheus metrics |
| POST | `/api/v1/projects` | write | Create a project |
| GET | `/api/v1/projects` | read | List projects (paginated) |
| GET | `/api/v1/projects/{slug}` | read | Get a project |
| DELETE | `/api/v1/projects/{slug}` | admin | Delete a project (cascades) |
| POST | `/api/v1/projects/{slug}/prompts` | write | Create a prompt |
| GET | `/api/v1/projects/{slug}/prompts` | read | List prompts (paginated) |
| GET | `/api/v1/projects/{slug}/prompts/{name}` | read | Get a prompt |
| DELETE | `/api/v1/projects/{slug}/prompts/{name}` | write | Delete a prompt |
| POST | `/api/v1/projects/{slug}/prompts/{name}/versions` | write | Add a version |
| GET | `/api/v1/projects/{slug}/prompts/{name}/versions` | read | List versions |
| GET | `/api/v1/projects/{slug}/prompts/{name}/resolve` | read | Resolve to a version |
| POST | `/api/v1/projects/{slug}/prompts/{name}/render` | read | Render with variables |
| PUT | `/api/v1/projects/{slug}/prompts/{name}/tags/{tag}` | write | Create or move a tag |
| GET | `/api/v1/projects/{slug}/prompts/{name}/tags` | read | List tags |
| DELETE | `/api/v1/projects/{slug}/prompts/{name}/tags/{tag}` | write | Delete a tag |
| POST | `/api/v1/api-keys` | admin | Issue a key (secret shown once) |
| GET | `/api/v1/projects/{slug}/api-keys` | admin | List a project's keys |
| DELETE | `/api/v1/api-keys/{key_id}` | admin | Revoke a key |

Pagination: list endpoints take `limit` (1 to 200, default 50) and `offset`
(default 0) query params, and return `{ "items": [...], "meta": { "total",
"limit", "offset" } }`.

Resolution: `/resolve` and `/render` accept `version` (integer) or `tag`
(string). If neither is given, the latest version is used. Precedence is
`version`, then `tag`, then latest.

---

## Walkthrough with curl

```bash
export BASE=http://localhost:8000
export FP_API_KEY=$(uv run floating-prompts bootstrap | tail -1)
auth=(-H "X-API-Key: $FP_API_KEY" -H "Content-Type: application/json")

# 1. Create a project
curl -s "${auth[@]}" -X POST "$BASE/api/v1/projects" \
  -d '{"slug":"acme","name":"ACME Corp"}'

# 2. Add version 1 (variables inferred from the template)
curl -s "${auth[@]}" -X POST \
  "$BASE/api/v1/projects/acme/prompts/summarizer/versions" \
  -d '{"user_prompt":"Summarize:\n\n{{ content }}","system_prompt":"Be concise."}'

# 3. Add version 2
curl -s "${auth[@]}" -X POST \
  "$BASE/api/v1/projects/acme/prompts/summarizer/versions" \
  -d '{"user_prompt":"TL;DR:\n\n{{ content }}"}'

# 4. Point the "production" tag at version 1
curl -s "${auth[@]}" -X PUT \
  "$BASE/api/v1/projects/acme/prompts/summarizer/tags/production" \
  -d '{"version":1}'

# 5. Render the production prompt
curl -s "${auth[@]}" -X POST \
  "$BASE/api/v1/projects/acme/prompts/summarizer/render" \
  -d '{"variables":{"content":"Hello world"},"tag":"production"}'
# -> {"name":"summarizer","version":1,"system_prompt":"Be concise.","user_prompt":"Summarize:\n\nHello world"}
```

---

## Request and response bodies

These mirror the Pydantic schemas in
`packages/sdk/src/floating_prompts_sdk/schemas/`.

**ProjectCreate**
```json
{ "slug": "acme", "name": "ACME Corp", "description": null }
```

**PromptVersionCreate** (omit `variables` to infer them from the template)
```json
{
  "user_prompt": "Summarize:\n\n{{ content }}",
  "system_prompt": "You are concise.",
  "variables": [{ "name": "content", "required": true, "description": null }]
}
```

**TagSet**
```json
{ "version": 1 }
```

**RenderRequest**
```json
{ "variables": { "content": "..." }, "version": null, "tag": "production" }
```

**RenderResult**
```json
{ "name": "summarizer", "version": 1, "system_prompt": "...", "user_prompt": "..." }
```

**ApiKeyCreate** (response includes `key` exactly once)
```json
{ "name": "ci-pipeline", "scopes": ["read", "write"], "project_slug": "acme" }
```

---

## Same flow with the SDK

```python
from floating_prompts_sdk import PromptsClient

with PromptsClient("http://localhost:8000", api_key="fp_...") as c:
    c.create_project("acme", "ACME Corp")
    c.create_version("acme", "summarizer",
                     user_prompt="Summarize:\n\n{{ content }}",
                     system_prompt="Be concise.")
    c.set_tag("acme", "summarizer", "production", version=1)
    result = c.render("acme", "summarizer", {"content": "Hello"}, tag="production")
    print(result.user_prompt)
```
