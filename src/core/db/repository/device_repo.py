"""Device repository."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.db.connection import get_session
from src.models.base import Device


class DeviceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_token_hash(self, token_hash: str) -> Device | None:
        return self.session.execute(
            select(Device).where(Device.token_hash == token_hash)
        ).scalar_one_or_none()

    def get_by_refresh_hash(self, refresh_hash: str) -> Device | None:
        return self.session.execute(
            select(Device).where(Device.refresh_hash == refresh_hash)
        ).scalar_one_or_none()

    def get_by_id_and_account(self, device_id: str, account_id: str) -> Device | None:
        return self.session.execute(
            select(Device).where(
                Device.id == device_id,
                Device.account_id == account_id,
            )
        ).scalar_one_or_none()

    def list_by_account(self, account_id: str) -> list[Device]:
        return list(
            self.session.execute(
                select(Device).where(Device.account_id == account_id)
            ).scalars().all()
        )

    def create(self, device: Device) -> Device:
        self.session.add(device)
        self.session.flush()
        return device

    def update(self) -> None:
        self.session.flush()


def get_device_repository(
    session: Annotated[Session, Depends(get_session)],
) -> DeviceRepository:
    return DeviceRepository(session)
