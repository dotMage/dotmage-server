"""Shared test fixtures."""

import os

# Must set before importing app
os.environ["DOTMAGE_DB_URL"] = "sqlite://"
os.environ["DOTMAGE_BOOTSTRAP_SECRET"] = "test-bootstrap-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from src.core.db.connection import get_session  # noqa: E402
from src.core.ratelimit import reset_rate_limits  # noqa: E402
from src.models.base import Base  # noqa: E402

# Single shared in-memory SQLite with StaticPool so all connections share the same db
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def _override_get_session():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


# Import app after env vars are set
from main import app  # noqa: E402

app.dependency_overrides[get_session] = _override_get_session


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(bind=_engine)
    reset_rate_limits()
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture()
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture()
def bootstrapped_client(client):
    """Client with account initialized. Returns (client, device_token, refresh_token)."""
    resp = client.post(
        "/api/v1/account/init",
        json={
            "bootstrap_secret": "test-bootstrap-secret",
            "salt": "dGVzdHNhbHQxMjM0NTY3OA==",
            "argon_memory": 65536,
            "argon_iterations": 3,
            "argon_parallelism": 1,
            "argon_version": 19,
            "nonce_ak": "dGVzdG5vbmNlMTIzNDU2Nzg5MDEyMzQ1Ng==",
            "wrapped_ak": "dGVzdHdyYXBwZWRhazEyMzQ1Njc4OTAxMjM0NTY=",
            "device_name": "test-device",
        },
    )
    assert resp.status_code == 201, f"Bootstrap failed: {resp.text}"
    data = resp.json()
    return client, data["device_token"], data["refresh_token"]
