from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Optional

from app.core.errors import ValidationError
from app.core.validation import require_fields, string_value

_TYPES = {"income", "direct_expense", "indirect_expense", "other_income", "finance_cost", "depreciation", "tax"}


@dataclass
class PLGroupInput:
    id: Optional[str] = None
    company_code: Optional[str] = None
    company_code_set: bool = False
    code: Optional[str] = None
    name: Optional[str] = None
    group_type: Optional[str] = None
    parent_id: Optional[str] = None
    parent_id_set: bool = False
    display_order: Optional[int] = None
    normal_direction: Optional[str] = None
    is_active: Optional[bool] = None


def _direction(body: dict) -> Optional[str]:
    explicit = string_value(body.get("normal_direction"))
    if explicit:
        explicit = explicit.lower()
        if explicit not in ("debit", "credit"):
            raise ValidationError("normal_direction must be debit or credit")
        return explicit
    legacy = string_value(body.get("type"))
    if not legacy:
        return None
    legacy = legacy.lower()
    return "credit" if legacy in ("revenue", "liability", "credit") else "debit"


def _display_order(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValidationError("display_order must be a non-negative integer")
    if parsed < 0:
        raise ValidationError("display_order must be a non-negative integer")
    return parsed


def _group_type(value: Any, normal_direction: Optional[str]) -> Optional[str]:
    if value is None:
        if normal_direction == "credit":
            return "income"
        if normal_direction:
            return "direct_expense"
        return None
    parsed = string_value(value)
    parsed = parsed.lower() if parsed else None
    if not parsed or parsed not in _TYPES:
        raise ValidationError("group_type is invalid")
    return parsed


def parse_create_pl_group(body: dict) -> PLGroupInput:
    group_id = string_value(body.get("id")) or f"plg_{uuid.uuid4()}"
    company_code = string_value(body.get("company_code")) or string_value(body.get("company_id")) or None
    code = (string_value(body.get("code")) or string_value(body.get("id")) or "").upper() or None
    name = (string_value(body.get("name")) or "").strip() or None
    require_fields({"code": code, "name": name}, ["code", "name"], "code and name are required")
    parent_id = None if body.get("parent_id") in (None, "") else string_value(body.get("parent_id"))
    if parent_id == group_id:
        raise ValidationError("parent_id cannot be self")
    normal_direction = _direction(body) or "debit"
    return PLGroupInput(
        id=group_id, company_code=company_code, code=code, name=name, parent_id=parent_id,
        display_order=_display_order(body.get("display_order")) or 0, normal_direction=normal_direction,
        group_type=_group_type(body.get("group_type"), normal_direction) or "direct_expense",
    )


def parse_update_pl_group(body: dict) -> PLGroupInput:
    parent_id_set = "parent_id" in body
    parent_id = None
    if parent_id_set:
        parent_id = None if body.get("parent_id") in (None, "") else string_value(body.get("parent_id"))
    name = None
    if "name" in body:
        name = (string_value(body.get("name")) or "").strip() or None
        if not name:
            raise ValidationError("name must be a non-empty string")
    code = None
    if "code" in body:
        code = (string_value(body.get("code")) or "").upper() or None
        if not code:
            raise ValidationError("code must be a non-empty string")
    if "is_active" in body and not isinstance(body.get("is_active"), bool):
        raise ValidationError("is_active must be a boolean")
    normal_direction = _direction(body)
    return PLGroupInput(
        name=name, code=code, parent_id=parent_id, parent_id_set=parent_id_set,
        display_order=_display_order(body.get("display_order")), normal_direction=normal_direction,
        group_type=_group_type(body.get("group_type"), normal_direction) if ("group_type" in body or normal_direction) else None,
        is_active=body.get("is_active"),
    )
