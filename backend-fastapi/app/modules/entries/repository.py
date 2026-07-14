from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.db.d1_client import D1Client


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class EntriesRepository:
    @staticmethod
    async def get_batch_by_id(d1: D1Client, batch_id: str) -> Optional[dict[str, Any]]:
        result = await d1.query("SELECT * FROM Entry_Batches WHERE id = ?", [batch_id])
        return result.rows[0] if result.rows else None

    @staticmethod
    async def get_ledger_entries_by_batch_id(d1: D1Client, batch_id: str) -> list[dict[str, Any]]:
        result = await d1.query("SELECT * FROM Ledger_Entries WHERE batch_id = ?", [batch_id])
        return result.rows

    @staticmethod
    async def get_ledger_entries_by_batch_ids(d1: D1Client, batch_ids: list[str]) -> list[dict[str, Any]]:
        if not batch_ids:
            return []
        placeholders = ", ".join("?" for _ in batch_ids)
        result = await d1.query(f"SELECT * FROM Ledger_Entries WHERE batch_id IN ({placeholders})", batch_ids)
        return result.rows

    @staticmethod
    async def create_batch_with_entries(
        d1: D1Client, batch: dict[str, Any], entries: list[dict[str, Any]]
    ) -> None:
        statements: list[tuple[str, list[Any]]] = [
            (
                """
                INSERT INTO Entry_Batches
                  (id, company_code, period, status, batch_type, business_unit_id, site_id, client_id,
                   vehicle_id, manager_id, reference, description, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    batch["id"], batch["company_code"], batch["period"], batch["status"], batch["batch_type"],
                    batch.get("business_unit_id"), batch.get("site_id"), batch.get("client_id"),
                    batch.get("vehicle_id"), batch.get("manager_id"), batch.get("reference"),
                    batch.get("description"), batch.get("created_by"), batch["created_at"], batch["updated_at"],
                ],
            )
        ]
        for entry in entries:
            statements.append(
                (
                    "INSERT INTO Ledger_Entries (id, batch_id, company_code, account_code, debit, credit, description) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [entry["id"], entry["batch_id"], entry["company_code"], entry["account_code"],
                     entry["debit"], entry["credit"], entry["description"]],
                )
            )
        await d1.batch(statements)

    @staticmethod
    async def list_by_company(
        d1: D1Client, company_code: str, filters: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        filters = filters or {}
        conditions = ["company_code = ?"]
        params: list[Any] = [company_code]
        if filters.get("period"):
            conditions.append("period = ?")
            params.append(filters["period"])
        if filters.get("status"):
            conditions.append("lower(status) = ?")
            params.append(filters["status"].lower())
        limit = min(max(filters.get("limit") or 200, 1), 500)
        params.append(limit)
        result = await d1.query(
            f"SELECT * FROM Entry_Batches WHERE {' AND '.join(conditions)} ORDER BY created_at DESC LIMIT ?",
            params,
        )
        return result.rows

    @staticmethod
    async def post_batch(d1: D1Client, batch_id: str, user_email: str, user_role: str) -> None:
        now = _now()
        await d1.batch([
            (
                "UPDATE Entry_Batches SET status = 'posted', posted_at = ?, posted_by = ?, updated_at = ? WHERE id = ?",
                [now, user_email, now, batch_id],
            ),
            (
                "INSERT INTO Audit_Logs (timestamp, user_email, role, action, details) VALUES (datetime('now'), ?, ?, 'POST_BATCH', ?)",
                [user_email, user_role, __import__("json").dumps({"batch_id": batch_id})],
            ),
        ])

    @staticmethod
    async def reverse_batch(
        d1: D1Client, original_batch: dict[str, Any], entries: list[dict[str, Any]],
        reversal_id: str, user_email: str, user_role: str,
    ) -> None:
        import json

        period = original_batch["created_at"][:7]
        now = _now()
        statements: list[tuple[str, list[Any]]] = [
            (
                """
                INSERT INTO Entry_Batches
                  (id, company_code, period, status, batch_type, business_unit_id, site_id, client_id,
                   vehicle_id, manager_id, created_at, updated_at, posted_at, original_batch_id)
                VALUES (?, ?, ?, 'posted', 'reversal', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    reversal_id, original_batch["company_code"], period,
                    original_batch.get("business_unit_id"), original_batch.get("site_id"),
                    original_batch.get("client_id"), original_batch.get("vehicle_id"), original_batch.get("manager_id"),
                    now, now, now, original_batch["id"],
                ],
            ),
        ]
        for entry in entries:
            statements.append(
                (
                    "INSERT INTO Ledger_Entries (id, batch_id, company_code, account_code, debit, credit, description) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?)",
                    [
                        f"entry-{uuid.uuid4()}", reversal_id, original_batch["company_code"], entry["account_code"],
                        entry["credit"], entry["debit"], f"Reversal: {entry.get('description') or ''}",
                    ],
                )
            )
        # Mark the original batch as reversed (replaces the old KV-based
        # "reversed_batch:<id>" flag -- there's no Cloudflare KV binding
        # available from Render, and a DB column is simpler/more durable).
        statements.append(
            ("UPDATE Entry_Batches SET reversal_batch_id = ?, updated_at = ? WHERE id = ?", [reversal_id, now, original_batch["id"]])
        )
        statements.append(
            (
                "INSERT INTO Audit_Logs (timestamp, user_email, role, action, details) VALUES (datetime('now'), ?, ?, 'REVERSE_BATCH', ?)",
                [user_email, user_role, json.dumps({"original_batch_id": original_batch["id"], "reversal_batch_id": reversal_id})],
            )
        )
        await d1.batch(statements)
