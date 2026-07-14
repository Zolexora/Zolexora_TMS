from __future__ import annotations
import json
from typing import Any
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.modules.audit.repository import AuditRepository


class AuditService:
    @staticmethod
    async def list(d1: D1Client, user: UserSession) -> list[dict[str, Any]]:
        logs = await AuditRepository.list_all(d1)
        if user.all_company_access:
            return logs
        visible = []
        for log in logs:
            details_raw = log.get("details")
            if not isinstance(details_raw, str):
                continue
            try:
                details = json.loads(details_raw)
            except (TypeError, ValueError):
                continue
            company_code = details.get("company_code") if isinstance(details, dict) else None
            if not isinstance(company_code, str):
                company_code = details.get("code") if isinstance(details, dict) else None
            if isinstance(company_code, str) and user.has_company_access(company_code):
                visible.append(log)
        return visible
