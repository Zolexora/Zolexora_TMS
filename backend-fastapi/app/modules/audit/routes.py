from __future__ import annotations
from fastapi import APIRouter, Depends
from app.core.security import UserSession, get_current_user
from app.db.d1_client import D1Client
from app.deps import get_d1
from app.modules.audit.service import AuditService

router = APIRouter(tags=["audit"])


@router.get("/audit-logs")
async def list_audit_logs(d1: D1Client = Depends(get_d1), user: UserSession = Depends(get_current_user)):
    return await AuditService.list(d1, user)
