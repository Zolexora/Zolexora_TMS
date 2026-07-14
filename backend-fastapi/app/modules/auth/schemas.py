from __future__ import annotations

from dataclasses import dataclass

from app.core.errors import ValidationError
from app.core.validation import require_fields, string_value

_VALID_ROLES = {"Admin", "FinanceAdmin", "Accountant", "DataEntry", "Viewer", "Auditor"}


@dataclass
class SetRoleInput:
    role: str


@dataclass
class CompanyAccessInput:
    company_code: str


def parse_set_role(body: dict) -> SetRoleInput:
    role = string_value(body.get("role"))
    require_fields({"role": role}, ["role"], "role is required")
    if role not in _VALID_ROLES:
        raise ValidationError(f"role must be one of {', '.join(sorted(_VALID_ROLES))}")
    return SetRoleInput(role=role)  # type: ignore[arg-type]


def parse_company_access(body: dict) -> CompanyAccessInput:
    company_code = string_value(body.get("company_code")) or string_value(body.get("company_id"))
    require_fields({"company_code": company_code}, ["company_code"], "company_code is required")
    return CompanyAccessInput(company_code=company_code)  # type: ignore[arg-type]
