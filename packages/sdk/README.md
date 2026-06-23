# floating-prompts-sdk

The typed Python SDK and API contract for the
[Floating Prompts](../../README.md) service. Depends only on `pydantic` and
`httpx` — no server-side dependencies — so it is safe to install in any consumer
application.

It contains:

- **`PromptsClient`** / **`AsyncPromptsClient`** — sync and async HTTP clients.
- **`schemas`** — the Pydantic request/response models (the API contract).
- **`Scope`** — the API-key permission enum.

```python
from floating_prompts_sdk import PromptsClient

with PromptsClient("http://localhost:8000", api_key="fp_...") as client:
    result = client.render("acme", "summarizer",
                           {"content": "Hello!"}, tag="production")
    print(result.user_prompt)
```

Errors are raised as `PromptsClientError` (carrying `.status`, `.code`, `.extra`
parsed from the service's RFC 9457 problem responses).
