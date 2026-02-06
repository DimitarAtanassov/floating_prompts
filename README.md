# 🗄️ Floating Prompts

Simple versioned prompt storage for LLM applications.

**Philosophy:** One table, minimal columns, maximum utility.

## What It Does

Stores prompts with versioning so you can:
- Track prompt changes over time
- Roll back to previous versions
- A/B test different prompt versions

```
┌─────────────────────────────────────────┐
│              prompts                    │
├─────────────────────────────────────────┤
│ id            UUID (auto)               │
│ name          "summarizer"              │
│ version       1, 2, 3...                │
│ system_prompt "You are helpful..."      │
│ user_prompt   "Summarize: {content}"    │
│ created_at    (auto)                    │
│ updated_at    (auto)                    │
└─────────────────────────────────────────┘
```

---

## Quick Start

```bash
# 1. Install
uv sync

# 2. Configure (create .env)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=floating_prompts

# 3. Start PostgreSQL
docker-compose up -d

# 4. Run migrations
uv run alembic upgrade head

# 5. Try it
uv run python main.py
```

---

## Usage

### Basic Operations

```python
from floating_prompts import Prompt, PromptRepository, get_session, init_db

# Initialize database (creates tables if needed)
init_db()

with get_session() as session:
    repo = PromptRepository(session)
    
    # Create a prompt (auto-increments version)
    prompt = repo.create(
        name="summarizer",
        system_prompt="You are a helpful assistant.",
        user_prompt="Summarize this: {content}",
    )
    
    # Get latest version of a prompt
    prompt = repo.get_by_name("summarizer")
    
    # Get specific version
    prompt = repo.get_by_name("summarizer", version=1)
    
    # List all versions of a prompt
    versions = repo.list_versions("summarizer")
    
    # List latest version of each prompt
    latest_prompts = repo.list_latest()
```

### Rendering Prompts

```python
# Get the prompt
prompt = repo.get_by_name("summarizer")

# Render with variables
system, user = prompt.render(content="Hello world!")
# system = "You are a helpful assistant."
# user = "Summarize this: Hello world!"

# Use with your LLM
response = llm.ask(user, system_prompt=system)
```

### Version Management

```python
# Create v1
repo.create(name="analyzer", user_prompt="Analyze: {text}")

# Create v2 (auto-increments)
repo.create(name="analyzer", user_prompt="Deep analysis: {text}")

# Create specific version
repo.create(name="analyzer", user_prompt="Quick analysis: {text}", version=10)

# List all versions
for p in repo.list_versions("analyzer"):
    print(f"v{p.version}: {p.user_prompt[:30]}...")
```

---

## Project Structure

```
floating_prompts/
├── src/floating_prompts/
│   ├── __init__.py      # Public API exports
│   ├── config.py        # Database settings from .env
│   ├── database.py      # Connection & session management
│   ├── repository.py    # CRUD operations
│   └── models/
│       ├── base.py      # SQLAlchemy base with UUID + timestamps
│       └── prompt.py    # The Prompt model
│
├── alembic/
│   └── versions/        # Database migrations
│
├── main.py              # Example usage
└── docker-compose.yml   # PostgreSQL container
```

---

## API Reference

### Prompt Model

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Auto-generated primary key |
| `name` | str | Prompt identifier (e.g., "summarizer") |
| `version` | int | Version number (default: 1) |
| `system_prompt` | str \| None | Optional system context |
| `user_prompt` | str | User prompt with `{placeholders}` |
| `created_at` | datetime | Auto-set on creation |
| `updated_at` | datetime | Auto-updated on changes |

### PromptRepository Methods

| Method | Description |
|--------|-------------|
| `create(name, user_prompt, system_prompt?, version?)` | Create a prompt |
| `get_by_name(name, version?)` | Get prompt (latest if no version) |
| `get_by_id(id)` | Get prompt by UUID |
| `list_all()` | List all prompts (all versions) |
| `list_names()` | List unique prompt names |
| `list_versions(name)` | List all versions of a prompt |
| `list_latest()` | List latest version of each prompt |
| `update(prompt, ...)` | Update prompt fields |
| `delete(prompt)` | Delete a prompt |
| `exists(name, version?)` | Check if prompt exists |

---

## Development

```bash
# Run linting
uv run ruff check src/ --fix
uv run ruff format src/

# Type checking
uv run mypy src/

# Run tests
uv run pytest
```

### Creating Migrations

```bash
# After changing models
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback one step
uv run alembic downgrade -1
```

---

## License

MIT