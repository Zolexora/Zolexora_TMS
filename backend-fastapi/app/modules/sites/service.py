from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.modules.audit.repository import AuditRepository
from app.modules.companies.repository import CompaniesRepository
from app.modules.sites.repository import SitesRepository
from app.modules.sites.schemas import CreateSiteInput, UpdateSiteInput

import uuid


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def present(site: dict[str, Any]) -> dict[str, Any]:
    return {**site}


async def _audit(d1: D1Client, user: UserSession, action: str, site: dict, before: Optional[dict] = None) -> None:
    details = {"company_code": site["company_code"], "site_id": site["id"], "after": present(site)}
    if before:
        details["before"] = present(before)
    await AuditRepository.log(d1, user_email=user.email, role=user.role, action=action, details=details)


class SitesService:
    @staticmethod
    async def list(pg: SupabasePostgres, company_code: str, user: UserSession) -> list[dict[str, Any]]:
        user.assert_company_access(company_code)
        if not await CompaniesRepository.exists(pg, company_code):
            raise NotFoundError("Company not found")
        return [present(s) for s in await SitesRepository.list(pg, company_code)]

    @staticmethod
    async def create(pg: SupabasePostgres, d1: D1Client, input: CreateSiteInput, user: UserSession) -> dict[str, Any]:
        user.assert_company_access(input.company_code)
        company = await CompaniesRepository.get_by_code(pg, input.company_code)
        if not company:
            raise NotFoundError("Company not found")
        if not company["is_active"]:
            raise ConflictError("Cannot add a site to an inactive company")
        if await SitesRepository.get_by_code(pg, input.company_code, input.site_code):
            raise ConflictError("Site code already exists in this company")

        unit_id = input.business_unit_id or await SitesRepository.ensure_primary_business_unit(pg, company)
        unit = await SitesRepository.get_business_unit(pg, unit_id)
        if not unit or unit["company_code"] != input.company_code or not unit["is_active"]:
            raise ValidationError("Business unit must be active and belong to the company")

        now = _now()
        site = {
            "id": f"site_{uuid.uuid4()}", "company_code": input.company_code, "business_unit_id": unit_id,
            "site_code": input.site_code, "site_name": input.site_name, "address": input.address,
            "is_active": True, "created_at": now, "updated_at": now,
        }
        await SitesRepository.create(pg, site)
        await _audit(d1, user, "CREATE_SITE", site)
        return present(site)

    @staticmethod
    async def update(pg: SupabasePostgres, d1: D1Client, site_id: str, input: UpdateSiteInput, user: UserSession) -> dict[str, Any]:
        current = await SitesRepository.get(pg, site_id)
        if not current:
            raise NotFoundError("Site not found")
        user.assert_company_access(current["company_code"])
        updated = {
            **current,
            "site_name": input.site_name if input.site_name is not None else current["site_name"],
            "address": input.address if input.address_set else current["address"],
            "is_active": current["is_active"] if input.is_active is None else input.is_active,
            "updated_at": _now(),
        }
        await SitesRepository.update(pg, updated)
        await _audit(d1, user, "UPDATE_SITE", updated, current)
        return present(updated)

    @staticmethod
    async def deactivate(pg: SupabasePostgres, d1: D1Client, site_id: str, user: UserSession) -> dict[str, Any]:
        return await SitesService.update(pg, d1, site_id, UpdateSiteInput(is_active=False), user)
