"""Application configuration parsed from environment variables."""

from __future__ import annotations

import hashlib
import re
import secrets
import string
import sys

from pydantic_settings import BaseSettings


def _parse_duration(value: str) -> int:
    """Parse a human duration string into seconds. E.g. '24h' -> 86400, '30d' -> 2592000."""
    m = re.fullmatch(r"(\d+)\s*([smhd])", value.strip())
    if not m:
        return int(value)
    amount = int(m.group(1))
    unit = m.group(2)
    multiplier = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return amount * multiplier[unit]


def _parse_rate_limit(value: str) -> int:
    """Parse rate limit like '10/min' -> 10."""
    parts = value.split("/")
    return int(parts[0])


class Settings(BaseSettings):
    DOTMAGE_DB_URL: str = "sqlite:////data/dotmage.db"
    DOTMAGE_BOOTSTRAP_SECRET: str = ""
    DOTMAGE_TOKEN_TTL: str = "24h"
    DOTMAGE_REFRESH_TTL: str = "30d"
    DOTMAGE_RATE_LIMIT: str = "10/min"
    DOTMAGE_LOG_LEVEL: str = "info"

    @property
    def token_ttl_seconds(self) -> int:
        return _parse_duration(self.DOTMAGE_TOKEN_TTL)

    @property
    def refresh_ttl_seconds(self) -> int:
        return _parse_duration(self.DOTMAGE_REFRESH_TTL)

    @property
    def rate_limit_count(self) -> int:
        return _parse_rate_limit(self.DOTMAGE_RATE_LIMIT)

    @property
    def bootstrap_secret(self) -> str:
        return self.DOTMAGE_BOOTSTRAP_SECRET

    @property
    def bootstrap_secret_hash(self) -> str:
        return hashlib.sha256(self.bootstrap_secret.encode()).hexdigest()


settings = Settings()

# Auto-generate bootstrap secret if not provided
if not settings.DOTMAGE_BOOTSTRAP_SECRET:
    alphabet = string.ascii_letters + string.digits
    generated = "".join(secrets.choice(alphabet) for _ in range(12))
    settings.DOTMAGE_BOOTSTRAP_SECRET = generated
    print(
        f"[dotMage] Generated bootstrap secret: {generated}",
        file=sys.stderr,
    )
