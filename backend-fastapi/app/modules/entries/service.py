from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from app.core.errors import AppError, NotFoundError, ValidationError
from app.core.security import UserSession
from app.db.d1_client import D1Client
from app.db.supabase_pg import SupabasePostgres
from app.modules.accounts.repository import AccountsRepository
from app.modules.audit.repository import AuditRepository
from app.modules.clients.repository import ClientsRepository
from app.modules.companies.repository import CompaniesRepository
from app.modules.entries.repository import EntriesRepository
from app.modules.entries.schemas import CreateEntryInput
from app.modules.managers.repository import ManagersRepository
from app.modules.periods.service import PeriodsService
from app.modules.sites.repository import SitesRepository
from app.modules.vehicles.repository import VehiclesRepository


def _business_type(company_type: Optional[str]) -> str:
    return (company_type or "").strip().lower()


def _is_transport_company(company_type: Optional[str]) -> bool:
    return "transport" in _business_type(company_type)


def _requires_site(company_type: Optional[str]) -> bool:
    normalized = _business_type(company_type)
    return any(k in normalized for k in ("transport", "hotel", "dairy"))


async def _resolve_site(pg: SupabasePostgres, company_code: str, input: CreateEntryInput) -> Optional[dict[str, Any]]:
    if not input.site_id and not input.site_code:
        return None
    site = (
        await SitesRepository.get(pg, input.site_id) if input.site_id
        else await SitesRepository.get_by_code(pg, company_code, input.site_code)  # type: ignore[arg-type]
    )
    if not site:
        field = "site_id" if input.site_id else "site_code"
        raise ValidationError("Site not found", [{"field": field, "message": "Unknown site"}])
    if site["company_code"] != company_code:
        raise ValidationError("Site belongs to another company")
    if not site["is_active"]:
        raise ValidationError("Site is inactive")
    if input.site_id and input.site_code:
        by_code = await SitesRepository.get_by_code(pg, company_code, input.site_code)
        if not by_code or by_code["id"] != site["id"]:
            raise ValidationError("Site id and site code do not match")
    return site


async def _resolve_client(pg: SupabasePostgres, company_code: str, input: CreateEntryInput) -> Optional[dict[str, Any]]:
    if not input.client_id and not input.client_code:
        return None
    client = (
        await ClientsRepository.get_by_id(pg, input.client_id) if input.client_id
        else await ClientsRepository.get_by_company_and_code(pg, company_code, input.client_code)  # type: ignore[arg-type]
    )
    if not client:
        field = "client_id" if input.client_id else "client_code"
        raise ValidationError("Client not found", [{"field": field, "message": "Unknown client"}])
    if client["company_code"] != company_code:
        raise ValidationError("Client belongs to another company")
    if not client["is_active"]:
        raise ValidationError("Client is inactive")
    if input.client_id and input.client_code:
        by_code = await ClientsRepository.get_by_company_and_code(pg, company_code, input.client_code)
        if not by_code or by_code["id"] != client["id"]:
            raise ValidationError("Client id and client code do not match")
    return client


async def _resolve_manager(pg: SupabasePostgres, company_code: str, input: CreateEntryInput) -> Optional[dict[str, Any]]:
    if not input.manager_id and not input.manager_code:
        return None
    manager = (
        await ManagersRepository.get_by_id(pg, input.manager_id) if input.manager_id
        else await ManagersRepository.get_by_company_and_code(pg, company_code, input.manager_code)  # type: ignore[arg-type]
    )
    if not manager:
        field = "manager_id" if input.manager_id else "manager_code"
        raise ValidationError("Manager not found", [{"field": field, "message": "Unknown manager"}])
    if manager["company_code"] != company_code:
        raise ValidationError("Manager belongs to another company")
    if not manager["is_active"]:
        raise ValidationError("Manager is inactive")
    if input.manager_id and input.manager_code:
        by_code = await ManagersRepository.get_by_company_and_code(pg, company_code, input.manager_code)
        if not by_code or by_code["id"] != manager["id"]:
            raise ValidationError("Manager id and manager code do not match")
    return manager


async def _resolve_vehicle(pg: SupabasePostgres, company_code: str, input: CreateEntryInput) -> Optional[dict[str, Any]]:
    if not input.vehicle_id and not input.vehicle_reg_no:
        return None
    vehicle = (
        await VehiclesRepository.get_by_id(pg, input.vehicle_id) if input.vehicle_id
        else await VehiclesRepository.get_by_company_and_registration(pg, company_code, input.vehicle_reg_no)  # type: ignore[arg-type]
    )
    if not vehicle:
        field = "vehicle_id" if input.vehicle_id else "vehicle_reg_no"
        raise ValidationError("Vehicle not found", [{"field": field, "message": "Unknown vehicle"}])
    if vehicle["company_code"] != company_code:
        raise ValidationError("Vehicle belongs to another company")
    if not vehicle["is_active"]:
        raise ValidationError("Vehicle is inactive")
    if input.vehicle_id and input.vehicle_reg_no:
        by_reg = await VehiclesRepository.get_by_company_and_registration(pg, company_code, input.vehicle_reg_no)
        if not by_reg or by_reg["id"] != vehicle["id"]:
            raise ValidationError("Vehicle id and vehicle registration number do not match")
    return vehicle


class EntriesService:
    @staticmethod
    async def create(
        pg: SupabasePostgres, d1: D1Client, input: CreateEntryInput, user: UserSession, dry_run: bool = False
    ) -> dict[str, Any]:
        user.assert_company_access(input.company_code)
        company = await CompaniesRepository.get_by_code(pg, input.company_code)
        if not company:
            raise ValidationError("Company not found", [{"field": "company_code", "message": "Unknown company"}])
        if not company["is_active"]:
            raise AppError(400, "Company is inactive", "Inactive companies cannot receive financial writes", "COMPANY_INACTIVE")

        site_required = _requires_site(company.get("business_type"))
        transport_required = _is_transport_company(company.get("business_type"))

        site = await _resolve_site(pg, input.company_code, input)
        client = await _resolve_client(pg, input.company_code, input)
        manager = await _resolve_manager(pg, input.company_code, input)
        vehicle = await _resolve_vehicle(pg, input.company_code, input)

        missing = []
        if site_required and not site:
            missing.append({"field": "site_code", "message": "Required"})
        if transport_required and not client:
            missing.append({"field": "client_code", "message": "Required"})
        if transport_required and not vehicle:
            missing.append({"field": "vehicle_reg_no", "message": "Required"})
        if transport_required and not manager:
            missing.append({"field": "manager_code", "message": "Required"})
        if missing:
            raise ValidationError("Missing required business dimensions", missing)

        if vehicle and site and vehicle["allocated_site_id"] != site["id"]:
            raise ValidationError("Vehicle must be allocated to the selected site", [{"field": "vehicle_reg_no", "message": "Vehicle/site mismatch"}])
        if vehicle and manager and vehicle["default_manager_id"] != manager["id"]:
            raise ValidationError("Vehicle must be assigned to the selected manager", [{"field": "vehicle_reg_no", "message": "Vehicle/manager mismatch"}])

        for index, entry in enumerate(input.entries):
            account = await AccountsRepository.get_by_company_and_code(pg, input.company_code, entry.account_code)
            if not account:
                raise ValidationError(f"Account {entry.account_code} does not exist", [{"field": f"entries.{index}.account_code", "message": "Unknown account"}])
            if not account["is_active"]:
                raise ValidationError(f"Account {entry.account_code} is inactive", [{"field": f"entries.{index}.account_code", "message": "Inactive account"}])

        period = input.created_at[:7]
        await PeriodsService.assert_open_period(pg, input.company_code, period)
        total_debit = sum(e.debit for e in input.entries)
        total_credit = sum(e.credit for e in input.entries)
        if abs(total_debit - total_credit) > 0.0001:
            raise AppError(400, "unbalanced entries in batch", "unbalanced entries in batch", "UNBALANCED_BATCH")

        batch = {
            "id": input.id, "company_code": input.company_code, "period": period, "status": "draft",
            "business_unit_id": (site or {}).get("business_unit_id") or input.business_unit_id,
            "site_id": (site or {}).get("id"), "client_id": (client or {}).get("id"),
            "vehicle_id": (vehicle or {}).get("id"), "manager_id": (manager or {}).get("id"),
            "reference": input.reference, "description": input.description, "created_by": user.email,
            "created_at": input.created_at, "updated_at": input.created_at, "batch_type": input.batch_type,
        }
        ledger_rows = [
            {
                "id": f"entry-{uuid.uuid4()}", "batch_id": input.id, "company_code": input.company_code,
                "account_code": e.account_code, "debit": e.debit, "credit": e.credit, "description": e.description,
            }
            for e in input.entries
        ]
        if not dry_run:
            await EntriesRepository.create_batch_with_entries(d1, batch, ledger_rows)

        saved_entries = [
            {"account_code": e.account_code, "account_id": e.account_code, "debit": e.debit, "credit": e.credit, "description": e.description}
            for e in input.entries
        ]
        return {
            "id": input.id, "company_code": input.company_code, "company_id": input.company_code,
            "status": "Draft", "reference": input.reference, "description": input.description,
            "created_by": user.email, "created_at": input.created_at,
            "business_unit_id": batch["business_unit_id"], "site_id": batch["site_id"],
            "client_id": batch["client_id"], "vehicle_id": batch["vehicle_id"], "manager_id": batch["manager_id"],
            "entries": saved_entries, "batch_type": input.batch_type,
        }

    @staticmethod
    async def list(
        pg: SupabasePostgres, d1: D1Client, company_code: str, user: UserSession,
        filters: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        user.assert_company_access(company_code)
        batches = await EntriesRepository.list_by_company(d1, company_code, filters)
        entries = await EntriesRepository.get_ledger_entries_by_batch_ids(d1, [b["id"] for b in batches])
        account_codes = sorted({e["account_code"] for e in entries})
        account_name_by_code: dict[str, str] = {}
        for code in account_codes:
            account = await AccountsRepository.get_by_company_and_code(pg, company_code, code)
            if account:
                account_name_by_code[code] = account["name"]

        entries_by_batch: dict[str, list[dict[str, Any]]] = {}
        for entry in entries:
            entries_by_batch.setdefault(entry["batch_id"], []).append(entry)

        results = []
        for batch in batches:
            lines = [
                {
                    "account_code": e["account_code"], "account_name": account_name_by_code.get(e["account_code"], e["account_code"]),
                    "debit": e["debit"], "credit": e["credit"], "description": e["description"],
                }
                for e in entries_by_batch.get(batch["id"], [])
            ]
            debit_total = sum(l["debit"] for l in lines)
            credit_total = sum(l["credit"] for l in lines)
            normalized_status = batch["status"].lower()
            status = "Posted" if normalized_status == "posted" else "Draft" if normalized_status == "draft" else ("Reversed" if batch["batch_type"] == "reversal" else batch["status"])
            results.append({
                "id": batch["id"], "company_code": batch["company_code"], "period": batch["period"],
                "reference": batch.get("reference"), "description": batch.get("description"), "status": status,
                "batch_type": batch["batch_type"], "created_by": batch.get("created_by"), "posted_by": batch.get("posted_by"),
                "created_at": batch["created_at"], "posted_at": batch.get("posted_at"),
                "original_batch_id": batch.get("original_batch_id"), "reversal_batch_id": batch.get("reversal_batch_id"),
                "debit_total": debit_total, "credit_total": credit_total, "lines": lines,
            })
        return results

    @staticmethod
    async def get(d1: D1Client, batch_id: str, user: UserSession) -> dict[str, Any]:
        batch = await EntriesRepository.get_batch_by_id(d1, batch_id)
        if not batch:
            raise NotFoundError("Batch not found")
        user.assert_company_access(batch["company_code"])
        entries = [{**e, "account_id": e["account_code"]} for e in await EntriesRepository.get_ledger_entries_by_batch_id(d1, batch_id)]
        normalized_status = batch["status"].lower()
        status = "Posted" if normalized_status == "posted" else "Draft" if normalized_status == "draft" else batch["status"]
        return {
            "id": batch["id"], "company_code": batch["company_code"], "company_id": batch["company_code"],
            "period": batch["period"], "status": status, "reference": batch.get("reference"),
            "description": batch.get("description"), "created_by": batch.get("created_by"), "posted_by": batch.get("posted_by"),
            "created_at": batch["created_at"], "posted_at": batch.get("posted_at"),
            "business_unit_id": batch.get("business_unit_id"), "site_id": batch.get("site_id"),
            "client_id": batch.get("client_id"), "vehicle_id": batch.get("vehicle_id"), "manager_id": batch.get("manager_id"),
            "batch_type": batch["batch_type"], "entries": entries,
        }

    @staticmethod
    async def post(pg: SupabasePostgres, d1: D1Client, batch_id: str, user: UserSession) -> dict[str, Any]:
        batch = await EntriesRepository.get_batch_by_id(d1, batch_id)
        if not batch:
            raise NotFoundError("Batch not found")
        user.assert_company_access(batch["company_code"])
        if batch["status"].lower() == "posted":
            raise AppError(400, "already posted", "already posted", "ALREADY_POSTED")
        await PeriodsService.assert_open_period(pg, batch["company_code"], batch["period"])
        await EntriesRepository.post_batch(d1, batch_id, user.email, user.role)
        return {"posted": True}

    @staticmethod
    async def reverse(pg: SupabasePostgres, d1: D1Client, batch_id: str, user: UserSession) -> dict[str, Any]:
        batch = await EntriesRepository.get_batch_by_id(d1, batch_id)
        if not batch:
            raise NotFoundError("Batch not found")
        user.assert_company_access(batch["company_code"])
        if batch["status"].lower() != "posted":
            raise ValidationError("Original batch is not posted")
        await PeriodsService.assert_open_period(pg, batch["company_code"], batch["period"])
        if batch.get("reversal_batch_id"):
            raise ValidationError("Batch already reversed")

        entries = await EntriesRepository.get_ledger_entries_by_batch_id(d1, batch_id)
        reversal_id = f"rev-{batch_id}-{int(time.time() * 1000)}"
        await EntriesRepository.reverse_batch(d1, batch, entries, reversal_id, user.email, user.role)
        return {"id": reversal_id, "status": "Posted", "message": "Reversal successful"}
