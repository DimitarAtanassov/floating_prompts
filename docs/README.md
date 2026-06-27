# Documentation

Start here to understand and run Floating Prompts.

| Doc | Read it to learn |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | The whole system: layers, request flow, subsystems, design decisions, and how to extend it. Best first read. |
| [DATABASE.md](DATABASE.md) | The PostgreSQL schema: ER diagram, every table, constraints, and migrations. |
| [API.md](API.md) | Every HTTP endpoint, auth, error format, and copy-paste curl and SDK examples. |

Also useful:

- [Web UI](../apps/web/): a React dashboard for projects, prompts, versions, tags,
  rendering. See the "Web UI" section of the root README to run it.
- [Root README](../README.md): one-paragraph overview and a 60-second quickstart.
- [CONTRIBUTING.md](../CONTRIBUTING.md): setup, workspace layout, and quality gates.
- [examples/quickstart.py](../examples/quickstart.py): a runnable SDK script.

## Suggested reading order for a new engineer

1. Root README (what and why).
2. ARCHITECTURE.md sections 1 to 7 (the mental model).
3. Run the onboarding checklist (ARCHITECTURE.md section 16).
4. API.md and DATABASE.md as reference while you explore the code.
5. ARCHITECTURE.md section 13 when you make your first change.

Diagrams in these docs use [Mermaid](https://mermaid.js.org/), which renders on
GitHub and in most IDE markdown previewers.
