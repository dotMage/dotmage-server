"""Simple in-memory rate limiter for auth endpoints."""

from __future__ import annotations

import time

from fastapi import HTTPException, Request

from app.core.config import settings

# IP -> (count, window_start_time)
_buckets: dict[str, tuple[int, float]] = {}
_WINDOW = 60.0  # 1 minute window


def check_rate_limit(request: Request) -> None:
    """FastAPI dependency that enforces per-IP rate limiting."""
    limit = settings.rate_limit_count
    ip = request.client.host if request.client else "unknown"
    now = time.monotonic()

    entry = _buckets.get(ip)
    if entry is None or now - entry[1] > _WINDOW:
        _buckets[ip] = (1, now)
        return

    count, window_start = entry
    if count >= limit:
        raise HTTPException(
            status_code=429,
            detail={"error": {"code": "rate_limited", "message": "Too many requests, try again later"}},
        )

    _buckets[ip] = (count + 1, window_start)


def reset_rate_limits() -> None:
    """Clear all buckets (useful for tests)."""
    _buckets.clear()
