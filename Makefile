# Floating Prompts, root orchestration Makefile.
# Python lives in apps/service + packages/sdk (uv workspace); the web UI in apps/web.

COMPOSE := docker compose
PY_SOURCES := apps packages
PY_SRC := apps/service/src packages/sdk/src
WEB := apps/web

.DEFAULT_GOAL := help

.PHONY: help
help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
.PHONY: prepare
prepare: ## Sync the locked uv workspace
	uv sync

.PHONY: frontend-install
frontend-install: ## Install web dependencies (npm)
	cd $(WEB) && npm install

# ---------------------------------------------------------------------------
# Quality gates (Python)
# ---------------------------------------------------------------------------
.PHONY: lintable
lintable: prepare ## Apply auto-formatting and auto-fixes
	uv run ruff format $(PY_SOURCES)
	uv run ruff check --fix $(PY_SOURCES)

.PHONY: lint
lint: prepare ## Run lint, format, and type checks
	uv lock --check
	uv run ruff format --check $(PY_SOURCES)
	uv run ruff check $(PY_SOURCES)
	uv run mypy $(PY_SRC)

.PHONY: typecheck
typecheck: prepare ## Run mypy only
	uv run mypy $(PY_SRC)

# ---------------------------------------------------------------------------
# Tests (need Docker for testcontainers)
# ---------------------------------------------------------------------------
.PHONY: test
test: prepare ## Run the full test suite with coverage
	uv run pytest --cov

.PHONY: test-unit
test-unit: prepare ## Run fast unit tests only (no Docker)
	uv run pytest -m unit

.PHONY: test-integration
test-integration: prepare ## Run integration tests (database)
	uv run pytest -m integration

.PHONY: test-e2e
test-e2e: prepare ## Run end-to-end API tests
	uv run pytest -m e2e

# ---------------------------------------------------------------------------
# Quality gates (Web)
# ---------------------------------------------------------------------------
.PHONY: frontend-lint
frontend-lint: ## Lint and type-check the web app
	cd $(WEB) && npm run lint && npm run typecheck

.PHONY: frontend-build
frontend-build: ## Production build of the web app
	cd $(WEB) && npm run build

.PHONY: gen-api
gen-api: ## Regenerate the web API types from the service OpenAPI
	cd $(WEB) && npm run gen:api

# ---------------------------------------------------------------------------
# Database & migrations
# ---------------------------------------------------------------------------
.PHONY: db
db: ## Start Postgres in the background
	$(COMPOSE) up -d postgres

.PHONY: db-down
db-down: ## Stop Postgres
	$(COMPOSE) stop postgres

.PHONY: migrate
migrate: ## Apply database migrations
	cd apps/service && uv run alembic upgrade head

.PHONY: revision
revision: ## Autogenerate a migration: make revision m="message"
	cd apps/service && uv run alembic revision --autogenerate -m "$(m)"

# ---------------------------------------------------------------------------
# Run services locally
# ---------------------------------------------------------------------------
.PHONY: serve
serve: ## Run the API (CORS enabled for the web dev server)
	FP_SERVER__CORS_ORIGINS='["http://localhost:5173"]' uv run floating-prompts serve

.PHONY: frontend
frontend: ## Run the web UI dev server (installs deps if needed)
	cd $(WEB) && { [ -d node_modules ] || npm install; } && npm run dev

.PHONY: dev
dev: db ## Start Postgres, migrate, then run API + frontend together
	$(MAKE) migrate
	$(MAKE) -j2 serve frontend

# ---------------------------------------------------------------------------
# Docker Compose stack
# ---------------------------------------------------------------------------
.PHONY: stack
stack: ## Build and run the full stack (postgres + api) via compose
	$(COMPOSE) --profile full up --build

.PHONY: down
down: ## Stop the stack (keep data volumes)
	$(COMPOSE) down

.PHONY: clean
clean: ## Stop the stack and delete data volumes
	$(COMPOSE) down -v

.PHONY: logs
logs: ## Tail logs from running services
	$(COMPOSE) logs -f

# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------
.PHONY: check
check: lint frontend-lint frontend-build test ## Run every gate (Python + frontend + tests)
