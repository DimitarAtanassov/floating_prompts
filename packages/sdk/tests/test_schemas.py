"""Unit tests for the SDK schemas (the API contract)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from floating_prompts_sdk import Page, ProjectRead, VariableSpec
from floating_prompts_sdk.schemas.common import PageMeta

pytestmark = pytest.mark.unit


def test_variable_spec_rejects_invalid_identifier() -> None:
    with pytest.raises(ValidationError):
        VariableSpec(name="not a name")


def test_variable_spec_defaults_required_true() -> None:
    assert VariableSpec(name="content").required is True


def test_generic_page_validates_items() -> None:
    page = Page[ProjectRead].model_validate(
        {
            "items": [
                {
                    "id": 1,
                    "slug": "acme",
                    "name": "ACME",
                    "description": None,
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                }
            ],
            "meta": {"total": 1, "limit": 50, "offset": 0},
        }
    )
    assert isinstance(page.meta, PageMeta)
    assert page.items[0].slug == "acme"
