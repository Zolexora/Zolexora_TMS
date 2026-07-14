from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from app.core.errors import ValidationError

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PERIOD_RE = re.compile(r"^\d{4}-\d{2}$")


@dataclass
class PLReportQuery:
    company_ids: list[str]
    company_value: str
    start: Optional[str] = None
    end: Optional[str] = None


def _validate_date(value: Optional[str], field: str) -> Optional[str]:
    if value is not None and not _DATE_RE.match(value):
        raise ValidationError(f"{field} must use YYYY-MM-DD", [{"field": field, "message": "Must use YYYY-MM-DD"}])
    return value


def parse_pl_report_query(query: dict[str, str]) -> PLReportQuery:
    company_value = query.get("company_code") or query.get("company_id") or query.get("company") or query.get("companies")
    if not company_value:
        raise ValidationError("company_code is required", [{"field": "company_code", "message": "Required"}])
    company_ids = [c.strip() for c in company_value.split(",") if c.strip()]
    if not company_ids:
        raise ValidationError("company_code is required", [{"field": "company_code", "message": "Required"}])

    start = _validate_date(query.get("start_date"), "start_date")
    end = _validate_date(query.get("end_date"), "end_date")
    if "period" in query:
        period = query["period"]
        if not _PERIOD_RE.match(period):
            raise ValidationError("period must use YYYY-MM", [{"field": "period", "message": "Must use YYYY-MM"}])
        start = f"{period}-01"
        end = f"{period}-31"
    return PLReportQuery(company_ids=company_ids, company_value=company_value, start=start, end=end)
