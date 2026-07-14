from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.core.errors import ConflictError, NotFoundError, ValidationError
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.modules.audit.repository import AuditRepository
from app.modules.auth.repository import AuthRepository
from app.modules.companies.repository import CompaniesRepository
from app.modules.companies.schemas import CreateCompanyInput, UpdateCompanyInput
from app.modules.pnl_groups.repository import PLGroupsRepository
from app.modules.sites.repository import SitesRepository


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def present(company: dict[str, Any]) -> dict[str, Any]:
    return {**company, "id": company["code"]}


class CompaniesService:
    @staticmethod
    async def create(pg: SupabasePostgres, d1: D1Client, input: CreateCompanyInput, user: UserSession) -> dict[str, Any]:
        if await CompaniesRepository.exists(pg, input.code):
            raise ConflictError(f"Company with code {input.code} already exists")

        now = _now()
        company = {
            "code": input.code, "name": input.name, "currency": input.currency,
            "fiscal_year_start": input.fiscal_year_start, "legal_name": input.legal_name,
            "business_type": input.business_type, "gst_number": input.gst_number,
            "pan_number": input.pan_number, "registered_address": input.registered_address,
            "logo_object_key": input.logo_object_key, "is_active": True,
            "created_at": now, "updated_at": now,
        }
        try:
            await CompaniesRepository.create(pg, company)
            await PLGroupsRepository.seed_defaults(pg, input.code)
            sites = await SitesRepository.create_primary_unit_with_sites(pg, company, input.sites)
        except Exception as exc:
            if isinstance(exc, ConflictError):
                raise
            raise ValidationError("Database constraint violation") from exc

        await AuditRepository.log(
            d1, user_email=user.email, role=user.role, action="CREATE_COMPANY",
            details={"company_code": input.code, "after": present(company), "sites": sites},
        )
        if not user.all_company_access:
            await AuthRepository.grant_company_access(pg, user.user_id, input.code)
        return {**present(company), "sites": sites}

    @staticmethod
    async def list(pg: SupabasePostgres, user: UserSession) -> list[dict[str, Any]]:
        companies = await CompaniesRepository.get_all(pg)
        return [present(c) for c in companies if user.has_company_access(c["code"])]

    @staticmethod
    async def get(pg: SupabasePostgres, code: str, user: UserSession) -> dict[str, Any]:
        user.assert_company_access(code)
        company = await CompaniesRepository.get_by_code(pg, code)
        if not company:
            raise NotFoundError("Company not found")
        return present(company)

    @staticmethod
    async def update(
        pg: SupabasePostgres, d1: D1Client, code: str, input: UpdateCompanyInput, user: UserSession
    ) -> dict[str, Any]:
        user.assert_company_access(code)
        current = await CompaniesRepository.get_by_code(pg, code)
        if not current:
            raise NotFoundError("Company not found")

        company = {
            "code": code,
            "name": input.name if input.name is not None else current["name"],
            "currency": input.currency if input.currency is not None else current["currency"],
            "fiscal_year_start": input.fiscal_year_start if input.fiscal_year_start is not None else current["fiscal_year_start"],
            "legal_name": input.legal_name if input.legal_name is not None else current["legal_name"],
            "business_type": input.business_type if input.business_type_set else current["business_type"],
            "gst_number": input.gst_number if input.gst_number_set else current["gst_number"],
            "pan_number": input.pan_number if input.pan_number_set else current["pan_number"],
            "registered_address": input.registered_address if input.registered_address_set else current["registered_address"],
            "logo_object_key": input.logo_object_key if input.logo_object_key_set else current["logo_object_key"],
            "is_active": current["is_active"] if input.is_active is None else input.is_active,
            "created_at": current["created_at"],
            "updated_at": _now(),
        }
        try:
            await CompaniesRepository.update(pg, code, company)
        except Exception as exc:
            raise ValidationError("Database constraint violation") from exc

        await AuditRepository.log(
            d1, user_email=user.email, role=user.role, action="UPDATE_COMPANY",
            details={"company_code": code, "before": present(current), "after": present(company)},
        )
        return present(company)

    @staticmethod
    async def deactivate(pg: SupabasePostgres, d1: D1Client, code: str, user: UserSession) -> dict[str, Any]:
        return await CompaniesService.update(pg, d1, code, UpdateCompanyInput(is_active=False), user)
