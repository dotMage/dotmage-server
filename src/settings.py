"""Application configuration parsed from environment variables."""

from __future__ import annotations

import hashlib
import re
import secrets
import string
import sys
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    model_config = SettingsConfigDict(
        env_prefix="DOTMAGE_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    DB_URL: str = "sqlite:////data/dotmage.db"
    BOOTSTRAP_SECRET: str = ""
    TOKEN_TTL: str = "24h"
    REFRESH_TTL: str = "30d"
    RATE_LIMIT: str = "10/min"
    LOG_LEVEL: str = "info"
    STATIC_DIR: str = "/app/static"

    @property
    def token_ttl_seconds(self) -> int:
        return _parse_duration(self.TOKEN_TTL)

    @property
    def refresh_ttl_seconds(self) -> int:
        return _parse_duration(self.REFRESH_TTL)

    @property
    def rate_limit_count(self) -> int:
        return _parse_rate_limit(self.RATE_LIMIT)

    @property
    def bootstrap_secret_hash(self) -> str:
        return hashlib.sha256(self.BOOTSTRAP_SECRET.encode()).hexdigest()


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _auto_generate_bootstrap() -> None:
    """Auto-generate bootstrap secret if not provided (called once at startup)."""
    settings = get_settings()
    if not settings.BOOTSTRAP_SECRET:
        alphabet = string.ascii_letters + string.digits
        generated = "".join(secrets.choice(alphabet) for _ in range(12))
        settings.BOOTSTRAP_SECRET = generated
        print(
            f"[dotMage] Generated bootstrap secret: {generated}",
            file=sys.stderr,
        )
