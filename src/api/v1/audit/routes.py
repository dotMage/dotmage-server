"""Audit log routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from src.api.dependencies.auth import require_device_token
from src.core.services.audit_service import AuditService, get_audit_service
from src.models.base import Device

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def audit_list(
    service: Annotated[AuditService, Depends(get_audit_service)],
    device: Device = Depends(require_device_token),
    limit: int = Query(default=100, le=1000),
    app: str | None = Query(default=None),
    env: str | None = Query(default=None),
) -> JSONResponse:
    result = service.list_events(
        device, app_name=app, env_name=env, limit=limit
    )
    return JSONResponse(status_code=200, content=result)
