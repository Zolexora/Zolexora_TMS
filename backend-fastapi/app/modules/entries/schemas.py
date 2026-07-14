from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.errors import ValidationError
from app.core.validation import string_value

_PERIOD_PREFIX_RE = re.compile(r"^\d{4}-\d{2}")


@dataclass
class EntryLineInput:
    account_code: str
    debit: float
    credit: float
    description: Optional[str]


@dataclass
class CreateEntryInput:
    id: str
    company_code: str
    reference: Optional[str]
    description: Optional[str]
    entries: list[EntryLineInput]
    created_at: str
    batch_type: str
    business_unit_id: Optional[str] = None
    site_id: Optional[str] = None
    site_code: Optional[str] = None
    client_id: Optional[str] = None
    client_code: Optional[str] = None
    vehicle_id: Optional[str] = None
    vehicle_reg_no: Optional[str] = None
    manager_id: Optional[str] = None
    manager_code: Optional[str] = None


def _amount(value: Any, field_name: str) -> float:
    if value is None or value == "":
        return 0.0
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        raise ValidationError("debit and credit values must be finite numbers", [{"field": field_name, "message": "Must be a finite number"}])
    if parsed < 0:
        raise ValidationError("debit and credit values must be non-negative", [{"field": field_name, "message": "Must be non-negative"}])
    return parsed


def _upper_or_none(value: Any) -> Optional[str]:
    s = string_value(value)
    return s.strip().upper() if s else None


def parse_create_entry(body: dict) -> CreateEntryInput:
    company_code = string_value(body.get("company_code")) or string_value(body.get("company_id"))
    raw_entries = body.get("entries")
    if not company_code or not isinstance(raw_entries, list) or len(raw_entries) == 0:
        details = []
        if not company_code:
            details.append({"field": "company_code", "message": "Required"})
        if not isinstance(raw_entries, list) or len(raw_entries) == 0:
            details.append({"field": "entries", "message": "Must be a non-empty array"})
        raise ValidationError("company_code and non-empty entries array are required", details)

    entries: list[EntryLineInput] = []
    for index, raw in enumerate(raw_entries):
        if not isinstance(raw, dict):
            raise ValidationError("Each entry must be an object", [{"field": f"entries.{index}", "message": "Must be an object"}])
        account_code = string_value(raw.get("account_code")) or string_value(raw.get("account_id"))
        if not account_code:
            raise ValidationError("account_code is required for all entries", [{"field": f"entries.{index}.account_code", "message": "Required"}])
        entries.append(
            EntryLineInput(
                account_code=account_code,
                debit=_amount(raw.get("debit"), f"entries.{index}.debit"),
                credit=_amount(raw.get("credit"), f"entries.{index}.credit"),
                description=string_value(raw.get("description")) or string_value(body.get("description")) or None,
            )
        )

    created_at = string_value(body.get("created_at")) or datetime.now(timezone.utc).isoformat()
    if not _PERIOD_PREFIX_RE.match(created_at):
        raise ValidationError("created_at must begin with YYYY-MM", [{"field": "created_at", "message": "Must begin with YYYY-MM"}])

    return CreateEntryInput(
        id=string_value(body.get("id")) or str(uuid.uuid4()),
        company_code=company_code,
        reference=string_value(body.get("reference")) or None,
        description=string_value(body.get("description")) or None,
        entries=entries,
        created_at=created_at,
        batch_type=string_value(body.get("batch_type")) or "standard",
        business_unit_id=string_value(body.get("business_unit_id")) or None,
        site_id=string_value(body.get("site_id")) or None,
        site_code=_upper_or_none(body.get("site_code")),
        client_id=string_value(body.get("client_id")) or None,
        client_code=_upper_or_none(body.get("client_code")),
        vehicle_id=string_value(body.get("vehicle_id")) or None,
        vehicle_reg_no=_upper_or_none(body.get("vehicle_reg_no")),
        manager_id=string_value(body.get("manager_id")) or None,
        manager_code=_upper_or_none(body.get("manager_code")),
    )
