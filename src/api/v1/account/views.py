"""Account request/response models."""

from __future__ import annotations

from pydantic import BaseModel


class AccountInitRequest(BaseModel):
    bootstrap_secret: str
    salt: str
    argon_memory: int = 65536
    argon_iterations: int = 3
    argon_parallelism: int = 1
    argon_version: int = 19
    nonce_ak: str
    wrapped_ak: str
    salt_rc: str | None = None
    nonce_rc: str | None = None
    wrapped_ak_rc: str | None = None
    device_name: str = "cli"


class PatchKeysRequest(BaseModel):
    nonce_ak: str
    wrapped_ak: str
    salt: str | None = None
