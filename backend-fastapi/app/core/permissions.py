"""Ported 1:1 from src/shared/permissions.ts. Keep in sync with the frontend's
route-permissions.ts if roles/permissions change.
"""
from __future__ import annotations

from typing import Literal

UserRole = Literal["Admin", "FinanceAdmin", "Accountant", "DataEntry", "Viewer", "Auditor"]

PERMISSIONS = {
    "COMPANY_MANAGE": "company:manage",
    "PL_GROUP_MANAGE": "pl-group:manage",
    "ACCOUNT_MANAGE": "account:manage",
    "ENTRY_CREATE": "entry:create",
    "ENTRY_POST": "entry:post",
    "ENTRY_REVERSE": "entry:reverse",
    "IMPORT_VALIDATE": "import:validate",
    "IMPORT_CONFIRM": "import:confirm",
    "PERIOD_LOCK": "period:lock",
    "PERIOD_UNLOCK": "period:unlock",
    "PERIOD_CLOSE": "period:close",
    "PERIOD_REOPEN": "period:reopen",
    "FINANCIAL_YEAR_MANAGE": "financial-year:manage",
}

_ALL = list(PERMISSIONS.values())

ROLE_PERMISSIONS: dict[UserRole, list[str]] = {
    "Admin": _ALL,
    "FinanceAdmin": [p for p in _ALL if p != PERMISSIONS["COMPANY_MANAGE"]],
    "Accountant": [
        PERMISSIONS["ACCOUNT_MANAGE"],
        PERMISSIONS["ENTRY_CREATE"],
        PERMISSIONS["ENTRY_POST"],
        PERMISSIONS["ENTRY_REVERSE"],
        PERMISSIONS["IMPORT_VALIDATE"],
        PERMISSIONS["IMPORT_CONFIRM"],
    ],
    "DataEntry": [PERMISSIONS["ENTRY_CREATE"], PERMISSIONS["IMPORT_VALIDATE"]],
    "Viewer": [],
    "Auditor": [],
}


def role_has_permission(role: str, permission: str) -> bool:
    return permission in ROLE_PERMISSIONS.get(role, [])
