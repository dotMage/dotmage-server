"""Revision request/response models."""

from __future__ import annotations

from pydantic import BaseModel


class PushRequest(BaseModel):
    blob: str
    content_hash: str | None = None
    parent_rev: int


class RollbackRequest(BaseModel):
    to_rev: int
