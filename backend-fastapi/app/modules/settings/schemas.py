from __future__ import annotations
from dataclasses import dataclass
from app.core.errors import ValidationError
from app.core.validation import require_fields, string_value
import re

_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


@dataclass
class PeriodLockInput:
    company_code: str
    period: str
    lock: bool


def parse_company_query(value: str | None) -> str:
    company_code = value.strip() if value else None
    if not company_code:
        raise ValidationError("company_code is required", [{"field": "company_code", "message": "Required"}])
    return company_code


def parse_period_lock(body: dict) -> PeriodLockInput:
    company_code = string_value(body.get("company_code")) or string_value(body.get("company_id"))
    period = string_value(body.get("period"))
    require_fields(
        {"company_code": company_code, "period": period, "lock": body.get("lock")},
        ["company_code", "period", "lock"], "company_code, period, and lock status are required",
    )
    if not _PERIOD_RE.match(period):  # type: ignore[arg-type]
        raise ValidationError("period must use YYYY-MM", [{"field": "period", "message": "Must use YYYY-MM"}])
    if not isinstance(body.get("lock"), bool):
        raise ValidationError("lock must be a boolean", [{"field": "lock", "message": "Must be a boolean"}])
    return PeriodLockInput(company_code=company_code, period=period, lock=body["lock"])  # type: ignore[arg-type]
