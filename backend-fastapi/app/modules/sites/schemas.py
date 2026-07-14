from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from app.core.errors import ValidationError
from app.core.validation import require_fields, string_value

_CODE_RE = re.compile(r"^[A-Z0-9_-]+$")


@dataclass
class NestedSiteInput:
    site_code: str
    site_name: str
    address: Optional[str]


@dataclass
class CreateSiteInput:
    company_code: str
    site_code: str
    site_name: str
    address: Optional[str]
    business_unit_id: Optional[str] = None


@dataclass
class UpdateSiteInput:
    site_name: Optional[str] = None
    address: Optional[str] = None
    address_set: bool = False
    is_active: Optional[bool] = None


def _clean_code(value: Any, field: str) -> str:
    code = (string_value(value) or "").strip().upper()
    if not code:
        raise ValidationError(f"{field} is required", [{"field": field, "message": "Required"}])
    if not _CODE_RE.match(code):
        raise ValidationError(f"{field} may contain letters, numbers, underscores, and hyphens only")
    return code


def _clean_name(value: Any, field: str) -> str:
    name = (string_value(value) or "").strip()
    if not name:
        raise ValidationError(f"{field} is required", [{"field": field, "message": "Required"}])
    return name


def _optional_string(value: Any, field: str) -> Optional[str]:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} must be a string")
    return value.strip() or None


def parse_nested_sites(value: Any) -> list[NestedSiteInput]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValidationError("sites must be an array")
    if len(value) > 50:
        raise ValidationError("A company can create at most 50 sites in one request")
    sites = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValidationError(f"sites.{index} must be an object")
        sites.append(
            NestedSiteInput(
                site_code=_clean_code(item.get("site_code", item.get("code")), f"sites.{index}.site_code"),
                site_name=_clean_name(item.get("site_name", item.get("name")), f"sites.{index}.site_name"),
                address=_optional_string(item.get("address"), f"sites.{index}.address"),
            )
        )
    if len({s.site_code for s in sites}) != len(sites):
        raise ValidationError("Site codes must be unique within the company request")
    return sites


def parse_create_site(body: dict) -> CreateSiteInput:
    company_code = string_value(body.get("company_code")) or string_value(body.get("company_id"))
    require_fields({"company_code": company_code}, ["company_code"], "company_code is required")
    return CreateSiteInput(
        company_code=company_code,  # type: ignore[arg-type]
        site_code=_clean_code(body.get("site_code", body.get("code")), "site_code"),
        site_name=_clean_name(body.get("site_name", body.get("name")), "site_name"),
        address=_optional_string(body.get("address"), "address"),
        business_unit_id=string_value(body.get("business_unit_id")),
    )


def parse_update_site(body: dict) -> UpdateSiteInput:
    site_name = None
    if "site_name" in body or "name" in body:
        site_name = _clean_name(body.get("site_name", body.get("name")), "site_name")
    if "is_active" in body and not isinstance(body.get("is_active"), bool):
        raise ValidationError("is_active must be a boolean")
    return UpdateSiteInput(
        site_name=site_name,
        address=_optional_string(body.get("address"), "address") if "address" in body else None,
        address_set="address" in body,
        is_active=body.get("is_active"),
    )
