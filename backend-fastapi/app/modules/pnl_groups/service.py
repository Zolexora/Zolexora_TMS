from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.modules.audit.repository import AuditRepository
from app.modules.companies.repository import CompaniesRepository
from app.modules.pnl_groups.repository import PLGroupsRepository
from app.modules.pnl_groups.schemas import PLGroupInput


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def present(group: dict[str, Any]) -> dict[str, Any]:
    return {**group, "type": "Revenue" if group["normal_direction"] == "credit" else "Expense"}


async def _would_create_cycle(pg: SupabasePostgres, group_id: str, parent_id: Optional[str]) -> bool:
    if not parent_id:
        return False
    visited = {group_id}
    current = parent_id
    while current:
        if current in visited:
            return True
        visited.add(current)
        current = await PLGroupsRepository.get_parent_id(pg, current)
    return False


async def _validate_parent(pg: SupabasePostgres, company_code: Optional[str], parent_id: Optional[str]) -> None:
    if not parent_id:
        return
    parent = await PLGroupsRepository.get_by_id(pg, parent_id)
    if not parent:
        raise ValidationError("Parent P&L group does not exist")
    if parent["company_code"] != company_code:
        raise ValidationError("Parent P&L group must belong to the same company")


async def _audit(d1: D1Client, user: UserSession, action: str, group: dict, before: Optional[dict] = None) -> None:
    details = {"company_code": group["company_code"], "pnl_group_id": group["id"], "after": present(group)}
    if before:
        details["before"] = present(before)
    await AuditRepository.log(d1, user_email=user.email, role=user.role, action=action, details=details)


class PLGroupsService:
    @staticmethod
    async def create(pg: SupabasePostgres, d1: D1Client, input: PLGroupInput, user: UserSession) -> dict[str, Any]:
        if input.company_code:
            user.assert_company_access(input.company_code)
            if not await CompaniesRepository.exists(pg, input.company_code):
                raise ValidationError("Company does not exist")
            if await PLGroupsRepository.get_by_company_and_code(pg, input.company_code, input.code):
                raise ConflictError("P&L group code already exists in this company")
        elif user.role != "Admin":
            raise ForbiddenError("Only Admin may manage legacy global groups")

        await _validate_parent(pg, input.company_code, input.parent_id)
        now = _now()
        group = {
            "id": input.id, "company_code": input.company_code, "code": input.code, "name": input.name,
            "group_type": input.group_type, "parent_id": input.parent_id, "display_order": input.display_order or 0,
            "normal_direction": input.normal_direction, "is_system": False, "is_active": True,
            "created_at": now, "updated_at": now,
        }
        try:
            await PLGroupsRepository.create(pg, group)
        except Exception as exc:
            raise ConflictError("P&L group ID or code already exists") from exc
        await _audit(d1, user, "CREATE_PL_GROUP", group)
        return present(group)

    @staticmethod
    async def list(pg: SupabasePostgres, company_code: Optional[str], user: UserSession) -> list[dict[str, Any]]:
        if company_code:
            user.assert_company_access(company_code)
        groups = await PLGroupsRepository.get_all(pg, company_code)
        visible = [
            g for g in groups
            if (user.role == "Admin" if g["company_code"] is None else user.has_company_access(g["company_code"]))
        ]
        return [present(g) for g in visible]

    @staticmethod
    async def get(pg: SupabasePostgres, group_id: str, user: UserSession) -> dict[str, Any]:
        group = await PLGroupsRepository.get_by_id(pg, group_id)
        if not group:
            raise NotFoundError("P&L group not found")
        if group["company_code"]:
            user.assert_company_access(group["company_code"])
        elif user.role != "Admin":
            raise ForbiddenError("Global group access is restricted")
        return present(group)

    @staticmethod
    async def update(pg: SupabasePostgres, d1: D1Client, group_id: str, input: PLGroupInput, user: UserSession) -> dict[str, Any]:
        current = await PLGroupsRepository.get_by_id(pg, group_id)
        if not current:
            raise NotFoundError("P&L group not found")
        if current["company_code"]:
            user.assert_company_access(current["company_code"])
        elif user.role != "Admin":
            raise ForbiddenError("Only Admin may manage legacy global groups")

        parent_id = input.parent_id if input.parent_id_set else current["parent_id"]
        await _validate_parent(pg, current["company_code"], parent_id)
        if await _would_create_cycle(pg, group_id, parent_id):
            raise ValidationError("Circular parent references are forbidden")

        code = input.code or current["code"]
        if current["company_code"] and code != current["code"] and await PLGroupsRepository.get_by_company_and_code(pg, current["company_code"], code):
            raise ConflictError("P&L group code already exists in this company")

        group = {
            **current, "code": code, "name": input.name or current["name"],
            "group_type": input.group_type or current["group_type"], "parent_id": parent_id,
            "display_order": input.display_order if input.display_order is not None else current["display_order"],
            "normal_direction": input.normal_direction or current["normal_direction"],
            "is_active": current["is_active"] if input.is_active is None else input.is_active,
            "updated_at": _now(),
        }
        await PLGroupsRepository.update(pg, group)
        await _audit(d1, user, "UPDATE_PL_GROUP", group, current)
        return present(group)

    @staticmethod
    async def deactivate(pg: SupabasePostgres, d1: D1Client, group_id: str, user: UserSession) -> dict[str, Any]:
        return await PLGroupsService.update(pg, d1, group_id, PLGroupInput(is_active=False), user)
