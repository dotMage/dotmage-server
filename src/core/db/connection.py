"""Database engine, session factory, and lifespan hooks."""

from __future__ import annotations

from collections.abc import Generator

from fastapi import FastAPI, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.settings import get_settings


def create_db_connection(app: FastAPI) -> None:
    """Create engine + session factory and store them on app.state."""
    settings = get_settings()
    connect_args: dict = {}
    if settings.DB_URL.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    eng = create_engine(settings.DB_URL, connect_args=connect_args)
    sf = sessionmaker(bind=eng, autoflush=False, expire_on_commit=False)

    app.state.engine = eng
    app.state.session_factory = sf

    from src.models.base import Base

    Base.metadata.create_all(bind=eng)


def shutdown_db_connection(app: FastAPI) -> None:
    """Dispose of the engine on shutdown."""
    app.state.engine.dispose()


def get_session(request: Request) -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session from the app-scoped factory."""
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()
