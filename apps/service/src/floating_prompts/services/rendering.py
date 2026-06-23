"""Safe prompt templating.

Templates use Jinja2 syntax (``{{ variable }}``) rendered through a
``SandboxedEnvironment`` with ``StrictUndefined``. Compared to the original
``str.format`` approach this:

* prevents template injection / attribute traversal (sandbox),
* fails loudly on missing variables instead of raising opaque ``KeyError`` /
  silently emitting blanks (``StrictUndefined``),
* validates supplied values against a declared variable contract.

The renderer is pure (no I/O), so it is trivially unit-testable and reusable by
both the service layer and the CLI.
"""

from __future__ import annotations

from dataclasses import dataclass

from jinja2 import StrictUndefined, TemplateError
from jinja2.meta import find_undeclared_variables
from jinja2.sandbox import SandboxedEnvironment

from floating_prompts.core.exceptions import ValidationError

__all__ = ["RenderedPrompt", "TemplateRenderer"]


@dataclass(frozen=True, slots=True)
class RenderedPrompt:
    """The result of rendering a prompt version."""

    system_prompt: str | None
    user_prompt: str


class TemplateRenderer:
    """Validates and renders prompt templates in a Jinja2 sandbox."""

    def __init__(self) -> None:
        self._env = SandboxedEnvironment(
            undefined=StrictUndefined,
            autoescape=False,  # prompts are plain text, not HTML
            keep_trailing_newline=True,
        )

    def referenced_variables(self, *templates: str | None) -> set[str]:
        """Return the variable names referenced across the given templates."""
        names: set[str] = set()
        for template in templates:
            if not template:
                continue
            ast = self._env.parse(template)
            names |= find_undeclared_variables(ast)
        return names

    def render(
        self,
        *,
        system_prompt: str | None,
        user_prompt: str,
        declared: set[str],
        required: set[str],
        values: dict[str, object],
    ) -> RenderedPrompt:
        """Validate ``values`` against the contract and render the templates.

        Raises:
            ValidationError: if unknown variables are supplied, required
                variables are missing, or a template fails to render.
        """
        provided = set(values)

        unknown = provided - declared
        if unknown:
            raise ValidationError(
                "Unknown template variables supplied.",
                code="unknown_variables",
                extra={"unknown": sorted(unknown), "declared": sorted(declared)},
            )

        missing = required - provided
        if missing:
            raise ValidationError(
                "Missing required template variables.",
                code="missing_variables",
                extra={"missing": sorted(missing)},
            )

        return RenderedPrompt(
            system_prompt=self._render_one(system_prompt, values),
            user_prompt=self._render_one(user_prompt, values) or "",
        )

    def _render_one(
        self, template: str | None, values: dict[str, object]
    ) -> str | None:
        if template is None:
            return None
        try:
            return self._env.from_string(template).render(**values)
        except TemplateError as exc:
            raise ValidationError(
                f"Template rendering failed: {exc}",
                code="template_error",
            ) from exc
