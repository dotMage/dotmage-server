"""Auth request/response models."""

from __future__ import annotations

from pydantic import BaseModel


class DeviceRegisterRequest(BaseModel):
    device_name: str = "cli"


class RefreshRequest(BaseModel):
    refresh_token: str
