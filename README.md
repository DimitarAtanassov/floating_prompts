# floating-prompts

Database layer for Prompt Management/Versioning services. Provides PostgreSQL models and migrations using SQLAlchemy 2.0.

## Features

- **SQLAlchemy 2.0** with modern type annotations
- **Alembic migrations** for schema versioning
- **UUID primary keys** for all entities
- **Automatic timestamps** (`created_at`, `updated_at`) on all tables

## Installation

```bash
# Clone and install
uv sync

# With development dependencies
uv sync --all-groups
```

## Configuration

Create a `.env` file:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
POSTGRES_DB=floating_prompts
```

## Quick Start

```bash
# Start PostgreSQL
docker-compose up -d

# Run migrations
uv run alembic upgrade head
```

---

## Database Schema

### Overview

The database is organized into two domains:

```
┌─────────────────────────────────────────────────────────────────────┐
│                           LLM DOMAIN                                │
│                                                                     │
│   LLMProvider ──1:N──▶ LLMModel ──1:N──▶ LLMConfig                  │
│   (openai)            (gpt-4)           (creative-writing)          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                │ referenced by
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          PROMPT DOMAIN                              │
│                                                                     │
│   PromptTemplate ──1:N──▶ PromptConfig ──1:N──▶ Prompt              │
│   (text content)          (schemas)            (rendered)           │
│                                                     │               │
│                                          ┌──────────┴──────────┐    │
│                                          │                     │    │
│                                          ▼                     ▼    │
│                                   PromptResponse          PromptTag │
│                                   (execution log)         (labels)  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

### LLM Domain

```
LLMProvider                 LLMModel                    LLMConfig
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ id              │────────▶│ id              │────────▶│ id              │
│ name            │   1:N   │ provider_id     │   1:N   │ model_id        │
│                 │         │ api_model_name  │         │ name            │
│                 │         │ display_name    │         │ temperature     │
│                 │         │ is_active       │         │ extra_settings  │
│                 │         │ is_deprecated   │         │ is_active       │
└─────────────────┘         └─────────────────┘         └─────────────────┘

Example:
  "openai"  ──▶  "gpt-4-turbo"  ──▶  "creative-writing" (temp=0.9)
                                 ──▶  "precise-extraction" (temp=0.1)
```

---

### Prompt Domain

```
PromptTemplate              PromptConfig                Prompt
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│ id              │────────▶│ id              │────────▶│ id              │
│ name            │   1:N   │ template_id     │   1:N   │ config_id       │
│ version         │         │ name            │         │ display_name    │
│ system_prompt   │         │ version         │         │ rendered_*      │
│ user_prompt     │         │ input_schema    │         │ environment     │
│ description     │         │ output_schema   │         │ is_active       │
└─────────────────┘         └─────────────────┘         │ category        │
                                                        └────────┬────────┘
                                                                 │
                                          ┌──────────────────────┼──────────────────────┐
                                          │ 1:N                  │ M:N                  │
                                          ▼                      ▼                      │
                            ┌─────────────────────┐    ┌─────────────────┐              │
                            │ PromptResponse      │    │ PromptTag       │              │
                            │─────────────────────│    │─────────────────│              │
                            │ id                  │    │ id              │              │
                            │ prompt_id           │    │ name            │◀─────────────┘
                            │ llm_config_id ──────│───▶│ description     │
                            │ llm_model_id ───────│───▶└─────────────────┘
                            │ llm_response        │         (via join table)
                            │ input_tokens        │
                            │ output_tokens       │
                            │ latency_ms          │
                            │ success             │
                            │ error_message       │
                            └─────────────────────┘
```

---

### Data Flow Example

```
1. CREATE TEMPLATE
   PromptTemplate(name="summarizer", version=1, user_prompt="Summarize: {text}")
                                        │
                                        ▼
2. CREATE CONFIG
   PromptConfig(template_id=..., input_schema={text: string}, output_format="json")
                                        │
                                        ▼
3. CREATE PROMPT
   Prompt(config_id=..., environment="production", rendered_user_prompt="Summarize: Hello world")
                                        │
                                        ▼
4. RECORD RESPONSE
   PromptResponse(prompt_id=..., llm_config_id=..., success=true, latency_ms=1200)
```

---

### Table Summary

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `llm_providers` | AI providers | `name` (openai, anthropic, google) |
| `llm_models` | Provider models | `api_model_name`, `is_active`, `is_deprecated` |
| `llm_configs` | Reusable settings | `temperature`, `extra_settings` |
| `prompt_templates` | Prompt text (versioned) | `name`, `version`, `system_prompt`, `user_prompt` |
| `prompt_configs` | Usage configuration | `input_schema`, `output_schema`, `output_format` |
| `prompts` | Rendered prompts | `rendered_*`, `environment`, `is_active` |
| `prompt_responses` | Execution logs | `llm_response`, `tokens`, `latency_ms`, `success` |
| `prompt_tags` | Categorization | `name`, `description` |

---

### Relationships

| From | To | Type | ON DELETE |
|------|-----|------|-----------|
| LLMProvider | LLMModel | 1:N | CASCADE |
| LLMModel | LLMConfig | 1:N | CASCADE |
| PromptTemplate | PromptConfig | 1:N | RESTRICT |
| PromptConfig | Prompt | 1:N | RESTRICT |
| Prompt | PromptResponse | 1:N | CASCADE |
| Prompt | PromptTag | M:N | CASCADE |
| PromptResponse | LLMConfig | N:1 | SET NULL |
| PromptResponse | LLMModel | N:1 | SET NULL |

---

### Key Design Decisions

**1. Immutable Templates**
```
New versions = new rows (like git commits)

summarizer v1  ──▶  summarizer v2  ──▶  summarizer v3
(original)          (improved)          (latest)
```

**2. Separation of Concerns**
```
Template  →  WHAT the prompt says
Config    →  HOW to validate it
Prompt    →  RENDERED instance
Response  →  EXECUTION result
```

**3. LLM Settings at Response Time**
```
Same prompt can use different models/settings.
Full audit trail of what produced what.
```

---

## Project Structure

```
floating_prompts/
├── src/floating_prompts/
│   ├── models/
│   │   ├── base.py          # Base model with id, timestamps
│   │   ├── llm.py           # LLMProvider, LLMModel, LLMConfig
│   │   └── prompt.py        # PromptTemplate, Config, Prompt, Response, Tag
│   ├── config.py            # Database settings (from .env)
│   └── __init__.py          # Public exports
├── alembic/
│   ├── versions/            # Migration files
│   └── env.py               # Migration config
└── docker-compose.yml       # PostgreSQL container
```

---

## Commands

| Command | Description |
|---------|-------------|
| `uv run alembic upgrade head` | Apply all migrations |
| `uv run alembic downgrade -1` | Rollback last migration |
| `uv run alembic revision --autogenerate -m "msg"` | Generate migration |
| `uv run alembic current` | Show current revision |
| `uv run alembic history` | Show migration history |

---

## Usage Examples

### Creating LLM Configuration

```python
from floating_prompts import LLMProvider, LLMModel, LLMConfig

provider = LLMProvider(name="openai")

model = LLMModel(
    provider=provider,
    api_model_name="gpt-4-turbo",
    display_name="GPT-4 Turbo",
    is_active=True,
)

config = LLMConfig(
    model=model,
    name="creative-writing",
    temperature=0.9,
    extra_settings={"max_tokens": 2000},
    is_active=True,
)
```

### Creating Prompts

```python
from floating_prompts import PromptTemplate, PromptConfig, Prompt

template = PromptTemplate(
    name="summarizer",
    version=1,
    system_prompt="You are a helpful assistant.",
    user_prompt="Summarize: {text}",
)

config = PromptConfig(
    template=template,
    name="summarizer-json",
    version=1,
    input_schema={"type": "object", "properties": {"text": {"type": "string"}}},
    output_format="json",
)

prompt = Prompt(
    config=config,
    display_name="Article Summarizer",
    environment="production",
    is_active=True,
)
```

### Recording Responses

```python
from floating_prompts import PromptResponse

response = PromptResponse(
    prompt=prompt,
    llm_config=config,
    llm_model=model,
    llm_response={"raw": "Summary: ...", "parsed": {"points": [...]}},
    input_tokens=150,
    output_tokens=50,
    latency_ms=1200,
    success=True,
)
```

---

## Common Queries

```sql
-- Get latest template version
SELECT * FROM prompt_templates 
WHERE name = 'summarizer' 
ORDER BY version DESC LIMIT 1;

-- Get active production prompts
SELECT p.*, pt.user_prompt
FROM prompts p
JOIN prompt_configs pc ON p.config_id = pc.id
JOIN prompt_templates pt ON pc.template_id = pt.id
WHERE p.environment = 'production' AND p.is_active = true;

-- Get response metrics
SELECT 
    COUNT(*) as total,
    AVG(latency_ms) as avg_latency,
    SUM(input_tokens + output_tokens) as total_tokens
FROM prompt_responses
WHERE prompt_id = 'uuid-here';
```