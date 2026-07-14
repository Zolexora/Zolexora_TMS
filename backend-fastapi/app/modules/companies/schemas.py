from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from app.core.errors import ValidationError
from app.core.validation import escape_html, require_fields, string_value
from app.modules.sites.schemas import NestedSiteInput, parse_nested_sites

_MONTH_MAX_DAYS = {1: 31, 2: 29, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
_FY_START_RE = re.compile(r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


@dataclass
class CreateCompanyInput:
    code: str
    name: str
    currency: str
    fiscal_year_start: str
    legal_name: str
    business_type: Optional[str]
    gst_number: Optional[str]
    pan_number: Optional[str]
    registered_address: Optional[str]
    logo_object_key: Optional[str]
    sites: list[NestedSiteInput]


@dataclass
class UpdateCompanyInput:
    name: Optional[str] = None
    currency: Optional[str] = None
    fiscal_year_start: Optional[str] = None
    legal_name: Optional[str] = None
    business_type: Optional[str] = None
    business_type_set: bool = False
    gst_number: Optional[str] = None
    gst_number_set: bool = False
    pan_number: Optional[str] = None
    pan_number_set: bool = False
    registered_address: Optional[str] = None
    registered_address_set: bool = False
    logo_object_key: Optional[str] = None
    logo_object_key_set: bool = False
    is_active: Optional[bool] = None


def is_valid_fiscal_year_start(value: Any) -> bool:
    if not isinstance(value, str) or not _FY_START_RE.match(value):
        return False
    month_text, day_text = value.split("-")
    return int(day_text) <= _MONTH_MAX_DAYS[int(month_text)]


def _nullable_string(value: Any) -> Optional[str]:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValidationError("Optional company fields must be strings")
    return value.strip() or None


def _nullable_escaped_string(value: Any) -> Optional[str]:
    normalized = _nullable_string(value)
    return escape_html(normalized) if normalized is not None else None


def parse_create_company(body: dict) -> CreateCompanyInput:
    code = string_value(body.get("code")) or string_value(body.get("id"))
    name = string_value(body.get("name"))
    require_fields({"code": code, "name": name}, ["code", "name"], "code and name are required")

    if code and len(code) > 100:
        raise ValidationError(
            "Company code length exceeds limit of 100", [{"field": "code", "message": "Must be 100 characters or fewer"}]
        )

    fiscal_year_start = string_value(body.get("fiscal_year_start")) or "01-01"
    if not is_valid_fiscal_year_start(fiscal_year_start):
        raise ValidationError(
            "Invalid fiscal_year_start format or date",
            [{"field": "fiscal_year_start", "message": "Use MM-DD with a valid calendar day"}],
        )

    currency = (string_value(body.get("currency")) or "USD").upper()
    if not _CURRENCY_RE.match(currency):
        raise ValidationError("currency must be a three-letter code", [{"field": "currency", "message": "Use an ISO-style three-letter code"}])

    return CreateCompanyInput(
        code=code,  # type: ignore[arg-type]
        name=escape_html(name),  # type: ignore[arg-type]
        currency=currency,
        fiscal_year_start=fiscal_year_start,
        legal_name=escape_html(string_value(body.get("legal_name")) or name),  # type: ignore[arg-type]
        business_type=_nullable_escaped_string(body.get("business_type")),
        gst_number=_nullable_escaped_string(body.get("gst_number")),
        pan_number=_nullable_escaped_string(body.get("pan_number")),
        registered_address=_nullable_escaped_string(body.get("registered_address")),
        logo_object_key=_nullable_string(body.get("logo_object_key")),
        sites=parse_nested_sites(body.get("sites")),
    )


def parse_update_company(body: dict) -> UpdateCompanyInput:
    if body.get("name") == "":
        raise ValidationError("Name cannot be empty", [{"field": "name", "message": "Cannot be empty"}])

    name = string_value(body.get("name")) if "name" in body else None
    if "name" in body and name is None:
        raise ValidationError("Name must be a string", [{"field": "name", "message": "Must be a string"}])

    currency = string_value(body.get("currency")) if "currency" in body else None
    if "currency" in body and currency is None:
        raise ValidationError("Currency must be a string", [{"field": "currency", "message": "Must be a string"}])
    normalized_currency = currency.upper() if currency else None
    if normalized_currency is not None and not _CURRENCY_RE.match(normalized_currency):
        raise ValidationError("currency must be a three-letter code", [{"field": "currency", "message": "Use an ISO-style three-letter code"}])

    fiscal_year_start = string_value(body.get("fiscal_year_start")) if "fiscal_year_start" in body else None
    if fiscal_year_start is not None and not is_valid_fiscal_year_start(fiscal_year_start):
        raise ValidationError(
            "Invalid fiscal_year_start format or date",
            [{"field": "fiscal_year_start", "message": "Use MM-DD with a valid calendar day"}],
        )

    legal_name = string_value(body.get("legal_name")) if "legal_name" in body else None
    if "legal_name" in body and not legal_name:
        raise ValidationError("Legal name cannot be empty", [{"field": "legal_name", "message": "Cannot be empty"}])

    if "is_active" in body and not isinstance(body.get("is_active"), bool):
        raise ValidationError("is_active must be a boolean", [{"field": "is_active", "message": "Must be a boolean"}])

    return UpdateCompanyInput(
        name=escape_html(name) if name is not None else None,
        currency=normalized_currency,
        fiscal_year_start=fiscal_year_start,
        legal_name=escape_html(legal_name) if legal_name is not None else None,
        business_type=_nullable_escaped_string(body.get("business_type")) if "business_type" in body else None,
        business_type_set="business_type" in body,
        gst_number=_nullable_escaped_string(body.get("gst_number")) if "gst_number" in body else None,
        gst_number_set="gst_number" in body,
        pan_number=_nullable_escaped_string(body.get("pan_number")) if "pan_number" in body else None,
        pan_number_set="pan_number" in body,
        registered_address=_nullable_escaped_string(body.get("registered_address")) if "registered_address" in body else None,
        registered_address_set="registered_address" in body,
        logo_object_key=_nullable_string(body.get("logo_object_key")) if "logo_object_key" in body else None,
        logo_object_key_set="logo_object_key" in body,
        is_active=body.get("is_active"),
    )
