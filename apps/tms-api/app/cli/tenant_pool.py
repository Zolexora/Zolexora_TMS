import argparse
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.config import settings

async def check_env():
    env = getattr(settings, "ENVIRONMENT", "development")
    if env == "production":
        return False
    return True

async def drop_tables(session: AsyncSession):
    tables = [
        "booking_requests", "bookings", "duties", "duty_assignments", "trips", "trip_events", 
        "rate_cards", "rate_card_versions", "rate_card_rules", "invoices", "invoice_lines", 
        "invoice_tax_lines", "payments", "payment_allocations", "payment_events", 
        "payables", "payable_lines", "settlements", "vendor_settlement_statements", 
        "expenses", "financial_snapshots", "financial_snapshot_lines", "billing_records", 
        "financial_periods", "financial_audit_logs", "financial_adjustment_notes", 
        "financial_adjustment_note_lines", "financial_adjustment_note_tax_lines", 
        "compliance_requirements", "compliance_records", "compliance_verifications", 
        "audit_logs", "customers", "vehicles", "drivers", "vendors"
    ]
    for t in tables:
        await session.execute(text(f"DROP TABLE IF EXISTS {t} CASCADE"))
    await session.commit()

async def delete_orgs(session: AsyncSession):
    await session.execute(text("DELETE FROM organisation_members"))
    await session.execute(text("DELETE FROM organisation_database_assignments"))
    await session.execute(text("DELETE FROM organisation_mongodb_assignments"))
    await session.execute(text("DELETE FROM organisation_storage_assignments"))
    await session.execute(text("DELETE FROM tenant_migration_jobs"))
    await session.execute(text("DELETE FROM platform_audit_logs"))
    await session.execute(text("DELETE FROM organisations"))
    await session.commit()

async def run_provision():
    async with AsyncSessionLocal() as session:
        await drop_tables(session)
        await delete_orgs(session)
    print("Cleanup successful.")

if __name__ == "__main__":
    asyncio.run(run_provision())
