"""Audit_Logs lives in D1 (it's an operational/transactional log), so every
module -- masters or transactional -- writes through here with a D1Client.
Mirrors src/backend/modules/audit/audit.repository.ts.
"""
from __future__ import annotations

import json
from typing import Any

from app.db.d1_client import D1Client


class AuditRepository:
    @staticmethod
    async def log(d1: D1Client, *, user_email: str, role: str, action: str, details: dict[str, Any]) -> None:
        await d1.query(
            "INSERT INTO Audit_Logs (timestamp, user_email, role, action, details) VALUES (datetime('now'), ?, ?, ?, ?)",
            [user_email, role, action, json.dumps(details, default=str)],
        )

    @staticmethod
    async def list_all(d1: D1Client, limit: int = 500) -> list[dict[str, Any]]:
        result = await d1.query("SELECT * FROM Audit_Logs ORDER BY timestamp DESC LIMIT ?", [limit])
        return result.rows
