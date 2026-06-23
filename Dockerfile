# syntax=docker/dockerfile:1

# --- Builder: resolve and install the service member with uv -----------------
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy just the manifests first so third-party deps cache across source changes.
COPY pyproject.toml uv.lock ./
COPY apps/service/pyproject.toml apps/service/README.md apps/service/
COPY packages/sdk/pyproject.toml packages/sdk/README.md packages/sdk/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-workspace --package floating-prompts-service

# Now copy sources and install the workspace members.
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package floating-prompts-service

# --- Runtime: slim image with just the venv and source -----------------------
FROM python:3.13-slim-bookworm AS runtime

RUN groupadd --system app && useradd --system --gid app app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Run from the service dir so Alembic finds alembic.ini.
WORKDIR /app/apps/service

USER app
EXPOSE 8000

# Apply migrations then serve.
CMD ["sh", "-c", "alembic upgrade head && uvicorn floating_prompts.api.app:create_app --factory --host 0.0.0.0 --port 8000"]
