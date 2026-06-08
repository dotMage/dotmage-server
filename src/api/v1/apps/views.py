"""App request/response models."""

from __future__ import annotations

from pydantic import BaseModel


class CreateAppRequest(BaseModel):
    name: str


class CreateEnvRequest(BaseModel):
    name: str
    copy_from: str | None = None
