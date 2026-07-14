from __future__ import annotations
from typing import Any
from app.core.errors import NotFoundError
from app.core.security import UserSession
from app.db.supabase_pg import SupabasePostgres
from app.modules.clients.repository import ClientsRepository
from app.modules.companies.repository import CompaniesRepository


def present(client: dict[str, Any]) -> dict[str, Any]:
    return {**client}


class ClientsService:
    @staticmethod
    async def list(pg: SupabasePostgres, company_code: str, user: UserSession) -> list[dict[str, Any]]:
        user.assert_company_access(company_code)
        if not await CompaniesRepository.exists(pg, company_code):
            raise NotFoundError("Company not found")
        return [present(c) for c in await ClientsRepository.list(pg, company_code)]
