from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.core.errors import ValidationError
from app.core.validation import require_fields, string_value


@dataclass
class CreateAccountInput:
    code: str
    company_code: str
    name: str
    pl_group_id: Optional[str]
    normal_direction: Optional[str]
    display_order: int
    balance: Optional[int] = None


@dataclass
class UpdateAccountInput:
    code: Optional[str] = None
    name: Optional[str] = None
    pl_group_id: Optional[str] = None
    pl_group_id_set: bool = False
    normal_direction: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    balance: Optional[int] = None
    balance_set: bool = False


def _integer(value: Any, field: str, optional: bool = True) -> Optional[int]:
    if value is None and optional:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be an integer")
    if field == "display_order" and parsed < 0:
        raise ValidationError(f"{field} must be an integer")
    return parsed


def _minor_units(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValidationError("balance must be a finite number")
    return round(parsed)


def _direction(value: Any) -> Optional[str]:
    if value is None:
        return None
    parsed = string_value(value)
    parsed = parsed.lower() if parsed else None
    if parsed not in ("debit", "credit"):
        raise ValidationError("normal_direction must be debit or credit")
    return parsed


def parse_create_account(body: dict) -> CreateAccountInput:
    code = string_value(body.get("code")) or string_value(body.get("id"))
    company_code = string_value(body.get("company_code")) or string_value(body.get("company_id"))
    name = (string_value(body.get("name")) or "").strip() or None
    require_fields(
        {"code": code, "company_code": company_code, "name": name},
        ["code", "company_code", "name"], "code, company_code, and name are required",
    )
    return CreateAccountInput(
        code=code, company_code=company_code, name=name,  # type: ignore[arg-type]
        pl_group_id=string_value(body.get("pl_group_id")) or None,
        normal_direction=_direction(body.get("normal_direction")),
        display_order=_integer(body.get("display_order", 0), "display_order", optional=False),  # type: ignore[arg-type]
        balance=_minor_units(body.get("balance")),
    )


def parse_update_account(body: dict) -> UpdateAccountInput:
    input = UpdateAccountInput(
        balance=_minor_units(body.get("balance")), balance_set="balance" in body,
        display_order=_integer(body.get("display_order"), "display_order"),
        normal_direction=_direction(body.get("normal_direction")),
    )
    if "code" in body:
        input.code = string_value(body.get("code"))
        if not input.code:
            raise ValidationError("code must be a non-empty string")
    if "name" in body:
        input.name = (string_value(body.get("name")) or "").strip() or None
        if not input.name:
            raise ValidationError("name must be a non-empty string")
    if "pl_group_id" in body:
        input.pl_group_id_set = True
        input.pl_group_id = None if body.get("pl_group_id") in (None, "") else string_value(body.get("pl_group_id"))
    if "is_active" in body and not isinstance(body.get("is_active"), bool):
        raise ValidationError("is_active must be a boolean")
    input.is_active = body.get("is_active")
    return input
