"""Token generation and hashing helpers."""

from __future__ import annotations

import hashlib
import secrets


def sha256_hash(value: str) -> str:
    """Return the SHA-256 hex digest of *value*."""
    return hashlib.sha256(value.encode()).hexdigest()


def generate_device_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash)."""
    raw = f"dmage_dtok_{secrets.token_hex(32)}"
    return raw, sha256_hash(raw)


def generate_refresh_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash)."""
    raw = f"dmage_rtok_{secrets.token_hex(32)}"
    return raw, sha256_hash(raw)


def generate_enrollment_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash)."""
    raw = f"dmage_etok_{secrets.token_hex(32)}"
    return raw, sha256_hash(raw)
