from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.core.errors import ValidationError
from app.core.validation import require_fields, string_value


@dataclass
class CreateFinancialYearInput:
    company_code: str
    name: str
    start_date: str
    end_date: str


@dataclass
class UpdateFinancialYearInput:
    name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: Optional[bool] = None


@dataclass
class PeriodTransitionInput:
    reason: Optional[str] = None


def parse_create_financial_year(body: dict) -> CreateFinancialYearInput:
    company_code = string_value(body.get("company_code")) or string_value(body.get("company_id"))
    name = string_value(body.get("name"))
    start_date = string_value(body.get("start_date"))
    end_date = string_value(body.get("end_date"))
    require_fields(
        {"company_code": company_code, "name": name, "start_date": start_date, "end_date": end_date},
        ["company_code", "name", "start_date", "end_date"],
        "company_code, name, start_date, and end_date are required",
    )
    return CreateFinancialYearInput(company_code=company_code, name=name, start_date=start_date, end_date=end_date)  # type: ignore[arg-type]


def parse_update_financial_year(body: dict) -> UpdateFinancialYearInput:
    if "is_active" in body and not isinstance(body.get("is_active"), bool):
        raise ValidationError("is_active must be a boolean")
    return UpdateFinancialYearInput(
        name=string_value(body.get("name")) if "name" in body else None,
        start_date=string_value(body.get("start_date")) if "start_date" in body else None,
        end_date=string_value(body.get("end_date")) if "end_date" in body else None,
        is_active=body.get("is_active"),
    )


def parse_period_transition(body: dict) -> PeriodTransitionInput:
    return PeriodTransitionInput(reason=string_value(body.get("reason")))
