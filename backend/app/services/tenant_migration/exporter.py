from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, MetaData
from typing import List, Dict, Any
from app.db.base import Base

class TenantDataExporter:
    """
    Exports data for a specific organisation from PostgreSQL.
    """
    def __init__(self, db: AsyncSession, organisation_id: str):
        self.db = db
        self.organisation_id = organisation_id
        
        # Explicitly define tenant tables to avoid exporting platform control plane tables
        self.tenant_tables = [
            "customers",
            "vendors",
            "drivers",
            "vehicles",
            "rate_cards",
            "rate_card_versions",
            "rate_card_rules",
            "booking_requests",
            "bookings",
            "duties",
            "duty_assignments",
            "trips",
            "trip_events",
            "financial_snapshots",
            "financial_snapshot_lines",
            "billing_records",
            "invoices",
            "invoice_lines",
            "invoice_tax_lines",
            "payments",
            "payment_allocations",
            "payment_events",
            "payables",
            "payable_lines",
            "settlements",
            "expenses",
            "compliance_records",
            "compliance_verifications",
            "financial_audit_logs",
            "audit_logs"
        ]

    async def get_table_schema(self) -> Dict[str, Any]:
        """
        Gets the schema for tenant tables. We rely on SQLAlchemy metadata.
        """
        schema = {}
        for table_name, table in Base.metadata.tables.items():
            if table_name in self.tenant_tables:
                schema[table_name] = table
        return schema

    async def export_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Exports rows for a single table associated with the organisation.
        """
        if table_name not in self.tenant_tables:
            raise ValueError(f"Table {table_name} is not a valid tenant table.")
            
        # All tenant tables must have organisation_id
        query = text(f"SELECT * FROM public.{table_name} WHERE organisation_id = :org_id")
        result = await self.db.execute(query, {"org_id": self.organisation_id})
        
        # Convert to list of dicts
        return [dict(row) for row in result.mappings()]

