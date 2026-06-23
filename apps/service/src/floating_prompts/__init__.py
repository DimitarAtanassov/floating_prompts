"""floating_prompts — the Floating Prompts service.

The deployable FastAPI application: prompt management with versioning, tags,
safe templating, API-key auth, and observability. The consumer-facing SDK and
the API schemas live in the separate ``floating_prompts_sdk`` package.

Build and run the app via :func:`floating_prompts.api.app.create_app` (or the
``floating-prompts`` CLI).
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0"
