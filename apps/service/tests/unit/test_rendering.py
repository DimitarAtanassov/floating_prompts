"""Unit tests for the templating engine (no I/O)."""

from __future__ import annotations

import pytest

from floating_prompts.core.exceptions import ValidationError
from floating_prompts.services.rendering import TemplateRenderer

pytestmark = pytest.mark.unit


@pytest.fixture
def renderer() -> TemplateRenderer:
    return TemplateRenderer()


def test_renders_system_and_user(renderer: TemplateRenderer) -> None:
    result = renderer.render(
        system_prompt="You are {{ role }}.",
        user_prompt="Hello {{ name }}",
        declared={"role", "name"},
        required={"role", "name"},
        values={"role": "helpful", "name": "Ada"},
    )
    assert result.system_prompt == "You are helpful."
    assert result.user_prompt == "Hello Ada"


def test_missing_required_variable_raises(renderer: TemplateRenderer) -> None:
    with pytest.raises(ValidationError) as exc:
        renderer.render(
            system_prompt=None,
            user_prompt="Hello {{ name }}",
            declared={"name"},
            required={"name"},
            values={},
        )
    assert exc.value.code == "missing_variables"
    assert exc.value.extra["missing"] == ["name"]


def test_unknown_variable_raises(renderer: TemplateRenderer) -> None:
    with pytest.raises(ValidationError) as exc:
        renderer.render(
            system_prompt=None,
            user_prompt="Hello {{ name }}",
            declared={"name"},
            required={"name"},
            values={"name": "Ada", "rogue": "x"},
        )
    assert exc.value.code == "unknown_variables"


def test_optional_variable_may_be_omitted(renderer: TemplateRenderer) -> None:
    result = renderer.render(
        system_prompt=None,
        user_prompt="Hi{{ ' ' ~ name if name else '' }}",
        declared={"name"},
        required=set(),
        values={"name": ""},
    )
    assert result.user_prompt == "Hi"


def test_referenced_variables_discovered(renderer: TemplateRenderer) -> None:
    names = renderer.referenced_variables("{{ a }}", "{{ b }} {{ c }}")
    assert names == {"a", "b", "c"}


def test_sandbox_blocks_attribute_escape(renderer: TemplateRenderer) -> None:
    with pytest.raises(ValidationError) as exc:
        renderer.render(
            system_prompt=None,
            user_prompt="{{ x.__class__.__mro__ }}",
            declared={"x"},
            required={"x"},
            values={"x": "abc"},
        )
    assert exc.value.code == "template_error"
