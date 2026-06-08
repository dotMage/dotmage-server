"""Account routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from src.api.dependencies.auth import optional_token, require_device_token
from src.api.v1.account.views import AccountInitRequest, PatchKeysRequest
from src.core.ratelimit import check_rate_limit
from src.core.services.account_service import AccountService, get_account_service
from src.models.base import Device

router = APIRouter(prefix="/account", tags=["account"])


@router.post("/init")
def account_init(
    body: AccountInitRequest,
    service: Annotated[AccountService, Depends(get_account_service)],
    _rl: None = Depends(check_rate_limit),
) -> JSONResponse:
    result = service.init_account(
        bootstrap_secret=body.bootstrap_secret,
        salt=body.salt,
        argon_memory=body.argon_memory,
        argon_iterations=body.argon_iterations,
        argon_parallelism=body.argon_parallelism,
        argon_version=body.argon_version,
        nonce_ak=body.nonce_ak,
        wrapped_ak=body.wrapped_ak,
        salt_rc=body.salt_rc,
        nonce_rc=body.nonce_rc,
        wrapped_ak_rc=body.wrapped_ak_rc,
        device_name=body.device_name,
    )
    return JSONResponse(
        status_code=201,
        content={
            "device_token": result.device_token,
            "refresh_token": result.refresh_token,
            "device_id": result.device_id,
            "token_expires_at": result.token_expires_at,
        },
    )


@router.get("/keys")
def account_keys_get(
    service: Annotated[AccountService, Depends(get_account_service)],
    device: Device | None = Depends(optional_token),
) -> JSONResponse:
    keys = service.get_keys(device)
    return JSONResponse(status_code=200, content=keys)


@router.patch("/keys")
def account_keys_patch(
    body: PatchKeysRequest,
    service: Annotated[AccountService, Depends(get_account_service)],
    device: Device = Depends(require_device_token),
) -> JSONResponse:
    result = service.patch_keys(
        device, nonce_ak=body.nonce_ak, wrapped_ak=body.wrapped_ak, salt=body.salt
    )
    return JSONResponse(status_code=200, content=result)
