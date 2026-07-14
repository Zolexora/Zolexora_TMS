from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.errors import ValidationError
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.modules.entries.schemas import parse_create_entry
from app.modules.entries.service import EntriesService
from app.modules.imports.schemas import (
    get_validation,
    parse_csv_rows,
    pop_validation,
    store_validation,
)


def _row_to_entry_payload(company_code: str, reference: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = rows[0]
    entry_date = first.get("entry_date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "id": f"import-{uuid.uuid4()}",
        "company_code": company_code,
        "reference": reference,
        "description": first.get("description") or None,
        "created_at": f"{entry_date}T00:00:00.000Z",
        "batch_type": "standard",
        "site_code": first.get("site_code") or None,
        "client_code": first.get("client_code") or None,
        "vehicle_reg_no": first.get("vehicle_reg_no") or None,
        "manager_code": first.get("manager_code") or None,
        "entries": [
            {
                "account_code": row.get("account_code"),
                "debit": row.get("debit") or 0,
                "credit": row.get("credit") or 0,
                "description": row.get("description") or None,
            }
            for row in rows
        ],
    }


class ImportsService:
    @staticmethod
    async def validate(
        pg: SupabasePostgres, d1: D1Client, company_code: str, raw_bytes: bytes, user: UserSession
    ) -> dict[str, Any]:
        user.assert_company_access(company_code)
        groups = parse_csv_rows(raw_bytes)

        results = []
        error_count = 0
        for reference, rows in groups.items():
            try:
                payload = _row_to_entry_payload(company_code, reference, rows)
                parsed = parse_create_entry(payload)
                preview = await EntriesService.create(pg, d1, parsed, user, dry_run=True)
                results.append({"batch_reference": reference, "row_count": len(rows), "valid": True, "preview": preview})
            except ValidationError as exc:
                error_count += 1
                results.append({"batch_reference": reference, "row_count": len(rows), "valid": False, "message": exc.message, "details": exc.details})

        validation_id = store_validation(company_code, groups)
        return {
            "validation_id": validation_id, "company_code": company_code,
            "total_batches": len(groups), "valid_batches": len(groups) - error_count,
            "invalid_batches": error_count, "results": results,
        }

    @staticmethod
    async def confirm(
        pg: SupabasePostgres, d1: D1Client, validation_id: str, company_code: str, user: UserSession
    ) -> dict[str, Any]:
        user.assert_company_access(company_code)
        session = pop_validation(validation_id, company_code)
        if not session:
            raise ValidationError("Validation session not found or expired; re-run validation")

        created, failed = [], []
        for reference, rows in session.groups.items():
            try:
                payload = _row_to_entry_payload(company_code, reference, rows)
                parsed = parse_create_entry(payload)
                result = await EntriesService.create(pg, d1, parsed, user, dry_run=False)
                created.append({"batch_reference": reference, "batch_id": result["id"]})
            except ValidationError as exc:
                failed.append({"batch_reference": reference, "message": exc.message})

        return {"company_code": company_code, "created": created, "failed": failed}
