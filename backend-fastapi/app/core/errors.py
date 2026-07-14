"""Application error hierarchy.

Mirrors src/backend/core/errors.ts from the original Worker so the JSON
error shape returned to the frontend is unchanged:
    {"error": "<Label>", "message": "...", "code": "...", "details": [...]}
"""
from __future__ import annotations

from typing import Any, Optional


class FieldError(dict):
    """A single field-level validation error: {"field": ..., "message": ...}."""

    def __init__(self, field: str, message: str):
        super().__init__(field=field, message=message)


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        label: str,
        message: str,
        code: Optional[str] = None,
        details: Optional[list[dict[str, Any]]] = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.label = label
        self.message = message
        self.code = code
        self.details = details or []

    def body(self, request_id: Optional[str] = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"error": self.label, "message": self.message}
        if request_id:
            payload["requestId"] = request_id
        if self.code:
            payload["code"] = self.code
        if self.details:
            payload["details"] = self.details
        return payload


class ValidationError(AppError):
    def __init__(self, message: str, details: Optional[list[dict[str, Any]]] = None):
        super().__init__(400, "Bad Request", message, "VALIDATION_ERROR", details)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(404, "Not Found", message, "NOT_FOUND")


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access denied"):
        super().__init__(403, "Forbidden", message, "FORBIDDEN")


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(401, "Unauthorized", message, "UNAUTHORIZED")


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "CONFLICT"):
        super().__init__(409, "Conflict", message, code)
