"""End-to-end SDK quickstart.

Prerequisites:
    1. docker compose up -d postgres
    2. uv run alembic upgrade head
    3. uv run floating-prompts serve            # in another terminal
    4. export FP_API_KEY=$(uv run floating-prompts bootstrap | tail -1)

Then:
    uv run python examples/quickstart.py
"""

from __future__ import annotations

import os

from floating_prompts_sdk import PromptsClient

API_URL = os.environ.get("FP_API_URL", "http://localhost:8000")
API_KEY = os.environ["FP_API_KEY"]


def main() -> None:
    with PromptsClient(API_URL, api_key=API_KEY) as client:
        client.create_project("demo", "Demo Project")

        # v1, then v2 — versions are immutable and auto-incrementing.
        client.create_version(
            "demo",
            "summarizer",
            user_prompt="Summarize the following:\n\n{{ content }}",
            system_prompt="You are a concise assistant.",
        )
        client.create_version(
            "demo", "summarizer", user_prompt="TL;DR in 3 bullets:\n\n{{ content }}"
        )

        # Pin a moving 'production' alias to v1.
        client.set_tag("demo", "summarizer", "production", version=1)

        result = client.render(
            "demo", "summarizer", {"content": "Hello, world!"}, tag="production"
        )
        print(f"Rendered v{result.version}:\n{result.user_prompt}")


if __name__ == "__main__":
    main()
