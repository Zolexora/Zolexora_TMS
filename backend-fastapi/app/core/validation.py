"""Mirrors src/backend/core/validation.ts. We parse JSON manually (rather
than relying on FastAPI's automatic Pydantic body validation) so malformed
or business-invalid bodies raise our own ValidationError and therefore
produce the exact same {error, message, code, details} JSON shape as every
other failure path -- not FastAPI's default 422 envelope.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import Request

from app.core.errors import ValidationError


async def read_json_object(request: Request, invalid_message: str = "Invalid JSON") -> dict[str, Any]:
    try:
        value = await request.json()
    except Exception as exc:
        raise ValidationError(invalid_message, [{"field": "$", "message": "Request body must be valid JSON"}]) from exc
    if not isinstance(value, dict):
        raise ValidationError(invalid_message, [{"field": "$", "message": "Request body must be a JSON object"}])
    return value


def string_value(value: Any) -> Optional[str]:
    return value if isinstance(value, str) else None


def require_fields(body: dict[str, Any], fields: list[str], message: str) -> None:
    details = [
        {"field": f, "message": "Required"}
        for f in fields
        if body.get(f) is None or body.get(f) == ""
    ]
    if details:
        raise ValidationError(message, details)


def escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )
