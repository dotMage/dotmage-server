"""Account repository."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.db.connection import get_session
from src.models.base import Account


class AccountRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_account(self) -> Account | None:
        return self.session.execute(select(Account)).scalar_one_or_none()

    def create(self, account: Account) -> Account:
        self.session.add(account)
        self.session.flush()
        return account

    def update(self) -> None:
        """Flush pending changes (attributes already mutated on the model)."""
        self.session.flush()


def get_account_repository(
    session: Annotated[Session, Depends(get_session)],
) -> AccountRepository:
    return AccountRepository(session)
