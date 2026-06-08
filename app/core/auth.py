"""Bearer-token auth middleware and token helpers."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Device
from app.db.session import get_db


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def generate_device_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash)."""
    raw = f"dmage_dtok_{secrets.token_hex(32)}"
    return raw, _sha256(raw)


def generate_refresh_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash)."""
    raw = f"dmage_rtok_{secrets.token_hex(32)}"
    return raw, _sha256(raw)


def generate_enrollment_token() -> tuple[str, str]:
    """Return (raw_token, sha256_hash). Enrollment tokens use a device record."""
    raw = f"dmage_etok_{secrets.token_hex(32)}"
    return raw, _sha256(raw)


def _extract_bearer(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return parts[1]


def require_device_token(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> Device:
    """FastAPI dependency: require a valid device token."""
    raw_token = _extract_bearer(authorization)
    if not raw_token:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "unauthorized", "message": "Missing or invalid Authorization header"}},
        )

    token_hash = _sha256(raw_token)
    device = db.execute(
        select(Device).where(Device.token_hash == token_hash)
    ).scalar_one_or_none()

    if device is None:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "unauthorized", "message": "Invalid token"}},
        )

    if device.revoked_at is not None:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "device_revoked", "message": "Device has been revoked"}},
        )

    now = datetime.now(timezone.utc)
    expires = device.token_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        raise HTTPException(
            status_code=401,
            detail={"error": {"code": "token_expired", "message": "Token has expired"}},
        )

    device.last_seen_at = now
    db.commit()

    return device


def optional_token(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> Device | None:
    """Accept any valid token (device or enrollment). Returns None if no auth header."""
    raw_token = _extract_bearer(authorization)
    if not raw_token:
        return None

    token_hash = _sha256(raw_token)
    device = db.execute(
        select(Device).where(Device.token_hash == token_hash)
    ).scalar_one_or_none()

    if device is None:
        return None

    if device.revoked_at is not None:
        return None

    now = datetime.now(timezone.utc)
    expires = device.token_expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires < now:
        return None

    device.last_seen_at = now
    db.commit()
    return device
