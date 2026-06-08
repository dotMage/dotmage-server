"""Revision repository."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.db.connection import get_session
from src.models.base import Revision


class RevisionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_env_and_number(
        self, environment_id: str, rev_number: int
    ) -> Revision | None:
        return self.session.execute(
            select(Revision).where(
                Revision.environment_id == environment_id,
                Revision.rev_number == rev_number,
            )
        ).scalar_one_or_none()

    def list_by_env(self, environment_id: str) -> list[Revision]:
        return list(
            self.session.execute(
                select(Revision)
                .where(Revision.environment_id == environment_id)
                .order_by(Revision.rev_number.desc())
            ).scalars().all()
        )

    def create(self, revision: Revision) -> Revision:
        self.session.add(revision)
        self.session.flush()
        return revision


def get_revision_repository(
    session: Annotated[Session, Depends(get_session)],
) -> RevisionRepository:
    return RevisionRepository(session)
