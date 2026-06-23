"""Unit tests for API-key generation and verification."""

from __future__ import annotations

import pytest

from floating_prompts.core import security

pytestmark = pytest.mark.unit


def test_generate_produces_consistent_derivatives() -> None:
    generated = security.generate_api_key(prefix_length=8)
    assert generated.plaintext.startswith("fp_")
    assert len(generated.prefix) == 8
    assert generated.plaintext.startswith(generated.prefix)
    assert security.verify_token(generated.plaintext, generated.token_hash)


def test_verify_rejects_wrong_key() -> None:
    generated = security.generate_api_key()
    assert not security.verify_token("fp_not-the-key", generated.token_hash)


def test_keys_are_unique() -> None:
    keys = {security.generate_api_key().plaintext for _ in range(100)}
    assert len(keys) == 100
