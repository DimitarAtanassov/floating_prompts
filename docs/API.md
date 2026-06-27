# API Reference

HTTP API for the Floating Prompts service. Use this to explore the service by
hand (curl) or to understand the SDK.

Interactive docs are also served live at `/docs` (Swagger) and `/redoc`.

Related docs: [Architecture](ARCHITECTURE.md), [Database schema](DATABASE.md).

---

## Base URL and versioning

All business endpoints are under `/api/v1`. Health and metrics endpoints live at
the root. The default local base URL is `http://localhost:8000`.

The API is currently **open** (no authentication). Restrict access at the network
or gateway layer for non-local deployments.

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
`missing_variables`, `unknown_variables`, `template_error`,
`request_validation_error`.

---

## Endpoint summary

| Method | Path | Purpose |
|---|---|---|
| GET | `/healthz` | Liveness |
| GET | `/readyz` | Readiness (checks DB) |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/v1/projects` | Create a project |
| GET | `/api/v1/projects` | List projects (paginated) |
| GET | `/api/v1/projects/{slug}` | Get a project |
| DELETE | `/api/v1/projects/{slug}` | Delete a project (cascades) |
| POST | `/api/v1/projects/{slug}/prompts` | Create a prompt |
| GET | `/api/v1/projects/{slug}/prompts` | List prompts (paginated) |
| GET | `/api/v1/projects/{slug}/prompts/{name}` | Get a prompt |
| DELETE | `/api/v1/projects/{slug}/prompts/{name}` | Delete a prompt |
| POST | `/api/v1/projects/{slug}/prompts/{name}/versions` | Add a version |
| GET | `/api/v1/projects/{slug}/prompts/{name}/versions` | List versions |
| GET | `/api/v1/projects/{slug}/prompts/{name}/resolve` | Resolve to a version |
| POST | `/api/v1/projects/{slug}/prompts/{name}/render` | Render with variables |
| PUT | `/api/v1/projects/{slug}/prompts/{name}/tags/{tag}` | Create or move a tag |
| GET | `/api/v1/projects/{slug}/prompts/{name}/tags` | List tags |
| DELETE | `/api/v1/projects/{slug}/prompts/{name}/tags/{tag}` | Delete a tag |

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
json=(-H "Content-Type: application/json")

# 1. Create a project
curl -s "${json[@]}" -X POST "$BASE/api/v1/projects" \
  -d '{"slug":"acme","name":"ACME Corp"}'

# 2. Add version 1 (variables inferred from the template)
curl -s "${json[@]}" -X POST \
  "$BASE/api/v1/projects/acme/prompts/summarizer/versions" \
  -d '{"user_prompt":"Summarize:\n\n{{ content }}","system_prompt":"Be concise."}'

# 3. Add version 2
curl -s "${json[@]}" -X POST \
  "$BASE/api/v1/projects/acme/prompts/summarizer/versions" \
  -d '{"user_prompt":"TL;DR:\n\n{{ content }}"}'

# 4. Point the "production" tag at version 1
curl -s "${json[@]}" -X PUT \
  "$BASE/api/v1/projects/acme/prompts/summarizer/tags/production" \
  -d '{"version":1}'

# 5. Render the production prompt
curl -s "${json[@]}" -X POST \
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

---

## Same flow with the SDK

```python
from floating_prompts_sdk import PromptsClient

with PromptsClient("http://localhost:8000") as c:
    c.create_project("acme", "ACME Corp")
    c.create_version("acme", "summarizer",
                     user_prompt="Summarize:\n\n{{ content }}",
                     system_prompt="Be concise.")
    c.set_tag("acme", "summarizer", "production", version=1)
    result = c.render("acme", "summarizer", {"content": "Hello"}, tag="production")
    print(result.user_prompt)
```
