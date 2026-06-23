"""API-key generation and verification.

A key is a single opaque string shown to the caller exactly once at creation:

    fp_<url-safe-random>

Only two derived values are persisted:

* ``prefix`` — the first N characters, stored in cleartext and indexed so a
  presented key can be located with a single equality lookup.
* ``token_hash`` — a SHA-256 hash of the full key. The plaintext is never
  stored, so a database leak does not expose usable credentials.

Verification recomputes the hash and compares it in constant time.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

__all__ = [
    "GeneratedApiKey",
    "extract_prefix",
    "generate_api_key",
    "hash_token",
    "verify_token",
]

_KEY_PREFIX = "fp_"


@dataclass(frozen=True, slots=True)
class GeneratedApiKey:
    """A freshly minted key and its persistable derivatives.

    ``plaintext`` must be returned to the caller immediately and then dropped;
    only ``prefix`` and ``token_hash`` are safe to store.
    """

    plaintext: str
    prefix: str
    token_hash: str


def hash_token(plaintext: str) -> str:
    """Return the hex SHA-256 digest of a key."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def extract_prefix(plaintext: str, prefix_length: int) -> str:
    """Return the indexable prefix of a key."""
    return plaintext[:prefix_length]


def generate_api_key(prefix_length: int = 8) -> GeneratedApiKey:
    """Generate a new API key and its persistable derivatives."""
    plaintext = f"{_KEY_PREFIX}{secrets.token_urlsafe(32)}"
    return GeneratedApiKey(
        plaintext=plaintext,
        prefix=extract_prefix(plaintext, prefix_length),
        token_hash=hash_token(plaintext),
    )


def verify_token(plaintext: str, expected_hash: str) -> bool:
    """Constant-time check that ``plaintext`` hashes to ``expected_hash``."""
    return hmac.compare_digest(hash_token(plaintext), expected_hash)
