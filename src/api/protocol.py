"""Shared API response helper."""

from __future__ import annotations

from fastapi.responses import JSONResponse


def make_response(content: dict, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=content)
