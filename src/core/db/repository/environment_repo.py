"""Environment repository."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.db.connection import get_session
from src.models.base import Environment


class EnvironmentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_app_and_name(self, app_id: str, name: str) -> Environment | None:
        return self.session.execute(
            select(Environment).where(
                Environment.app_id == app_id,
                Environment.name == name,
            )
        ).scalar_one_or_none()

    def list_by_app(self, app_id: str) -> list[Environment]:
        return list(
            self.session.execute(
                select(Environment).where(Environment.app_id == app_id)
            ).scalars().all()
        )

    def create(self, env: Environment) -> Environment:
        self.session.add(env)
        self.session.flush()
        return env

    def delete(self, env: Environment) -> None:
        self.session.delete(env)
        self.session.flush()


def get_environment_repository(
    session: Annotated[Session, Depends(get_session)],
) -> EnvironmentRepository:
    return EnvironmentRepository(session)
