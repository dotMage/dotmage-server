"""App and environment CRUD endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import require_device_token
from app.db.models import App, AuditLog, Device, Environment, Revision
from app.db.session import get_db

router = APIRouter(prefix="/apps", tags=["apps"])


class CreateAppBody(BaseModel):
    name: str


class CreateEnvBody(BaseModel):
    name: str
    copy_from: str | None = None


@router.get("")
def apps_list(
    db: Session = Depends(get_db),
    device: Device = Depends(require_device_token),
) -> JSONResponse:
    apps = db.execute(
        select(App).where(App.account_id == device.account_id)
    ).scalars().all()

    result = []
    for a in apps:
        envs = db.execute(
            select(Environment).where(Environment.app_id == a.id)
        ).scalars().all()
        result.append({
            "id": a.id,
            "name": a.name,
            "created_at": a.created_at.isoformat() + "Z",
            "updated_at": a.updated_at.isoformat() + "Z",
            "environments": [
                {
                    "id": e.id,
                    "name": e.name,
                    "latest_rev": e.latest_rev,
                    "protected": e.protected,
                    "created_at": e.created_at.isoformat() + "Z",
                    "updated_at": e.updated_at.isoformat() + "Z",
                }
                for e in envs
            ],
        })

    return JSONResponse(status_code=200, content={"apps": result})


@router.post("")
def apps_create(
    body: CreateAppBody,
    db: Session = Depends(get_db),
    device: Device = Depends(require_device_token),
) -> JSONResponse:
    # Check uniqueness
    existing = db.execute(
        select(App).where(
            App.account_id == device.account_id,
            App.name == body.name,
        )
    ).scalar_one_or_none()

    if existing is not None:
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "app_exists", "message": f"App '{body.name}' already exists"}},
        )

    now = datetime.now(timezone.utc)
    app = App(
        account_id=device.account_id,
        name=body.name,
        created_at=now,
        updated_at=now,
    )
    db.add(app)

    audit = AuditLog(
        account_id=device.account_id,
        device_id=device.id,
        action="app.created",
        app_name=body.name,
        created_at=now,
    )
    db.add(audit)
    db.commit()

    return JSONResponse(
        status_code=201,
        content={
            "id": app.id,
            "name": app.name,
            "created_at": app.created_at.isoformat() + "Z",
            "updated_at": app.updated_at.isoformat() + "Z",
        },
    )


def _get_app_by_name(db: Session, account_id: str, name: str) -> App | None:
    return db.execute(
        select(App).where(App.account_id == account_id, App.name == name)
    ).scalar_one_or_none()


@router.get("/{name}/envs")
def envs_list(
    name: str,
    db: Session = Depends(get_db),
    device: Device = Depends(require_device_token),
) -> JSONResponse:
    app = _get_app_by_name(db, device.account_id, name)
    if app is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "not_found", "message": f"App '{name}' not found"}},
        )

    envs = db.execute(
        select(Environment).where(Environment.app_id == app.id)
    ).scalars().all()

    return JSONResponse(
        status_code=200,
        content={
            "environments": [
                {
                    "id": e.id,
                    "name": e.name,
                    "latest_rev": e.latest_rev,
                    "protected": e.protected,
                    "created_at": e.created_at.isoformat() + "Z",
                    "updated_at": e.updated_at.isoformat() + "Z",
                }
                for e in envs
            ]
        },
    )


@router.post("/{name}/envs")
def envs_create(
    name: str,
    body: CreateEnvBody,
    db: Session = Depends(get_db),
    device: Device = Depends(require_device_token),
) -> JSONResponse:
    app = _get_app_by_name(db, device.account_id, name)
    if app is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "not_found", "message": f"App '{name}' not found"}},
        )

    # Check uniqueness
    existing = db.execute(
        select(Environment).where(
            Environment.app_id == app.id,
            Environment.name == body.name,
        )
    ).scalar_one_or_none()

    if existing is not None:
        return JSONResponse(
            status_code=409,
            content={"error": {"code": "env_exists", "message": f"Environment '{body.name}' already exists"}},
        )

    now = datetime.now(timezone.utc)
    env = Environment(
        app_id=app.id,
        name=body.name,
        created_at=now,
        updated_at=now,
    )
    db.add(env)
    db.flush()

    # If copy_from, copy the latest revision from the source env
    if body.copy_from:
        source_env = db.execute(
            select(Environment).where(
                Environment.app_id == app.id,
                Environment.name == body.copy_from,
            )
        ).scalar_one_or_none()

        if source_env is None:
            return JSONResponse(
                status_code=404,
                content={"error": {"code": "not_found", "message": f"Source environment '{body.copy_from}' not found"}},
            )

        if source_env.latest_rev > 0:
            source_rev = db.execute(
                select(Revision).where(
                    Revision.environment_id == source_env.id,
                    Revision.rev_number == source_env.latest_rev,
                )
            ).scalar_one_or_none()

            if source_rev:
                new_rev = Revision(
                    environment_id=env.id,
                    rev_number=1,
                    blob=source_rev.blob,
                    parent_rev=None,
                    device_id=device.id,
                    created_at=now,
                )
                db.add(new_rev)
                env.latest_rev = 1

    audit = AuditLog(
        account_id=device.account_id,
        device_id=device.id,
        action="env.created",
        app_name=name,
        env_name=body.name,
        created_at=now,
    )
    db.add(audit)
    db.commit()

    return JSONResponse(
        status_code=201,
        content={
            "id": env.id,
            "name": env.name,
            "latest_rev": env.latest_rev,
            "protected": env.protected,
            "created_at": env.created_at.isoformat() + "Z",
            "updated_at": env.updated_at.isoformat() + "Z",
        },
    )


@router.delete("/{name}/envs/{env}")
def envs_delete(
    name: str,
    env: str,
    db: Session = Depends(get_db),
    device: Device = Depends(require_device_token),
) -> JSONResponse:
    app = _get_app_by_name(db, device.account_id, name)
    if app is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "not_found", "message": f"App '{name}' not found"}},
        )

    environment = db.execute(
        select(Environment).where(
            Environment.app_id == app.id,
            Environment.name == env,
        )
    ).scalar_one_or_none()

    if environment is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "not_found", "message": f"Environment '{env}' not found"}},
        )

    now = datetime.now(timezone.utc)
    audit = AuditLog(
        account_id=device.account_id,
        device_id=device.id,
        action="env.deleted",
        app_name=name,
        env_name=env,
        created_at=now,
    )
    db.add(audit)

    db.delete(environment)
    db.commit()

    return JSONResponse(status_code=200, content={"ok": True})
