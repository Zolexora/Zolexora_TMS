"""
Seed Zolexora Platform Role Templates.
Run: uv run python -m app.modules.identity.roles.seed_platform_templates
"""

import asyncio
import uuid
from app.db.session import AsyncSessionLocal
from app.modules.identity.roles.models import PlatformRoleTemplate, PlatformRoleTemplatePermission


# Define the canonical Zolexora platform role templates.
# Organizations can copy these but never modify the originals.
PLATFORM_TEMPLATES = [
    {
        "code": "operations_manager",
        "name": "Operations Manager",
        "description": "Full access to all operational modules: bookings, dispatch, duties, fleet, and CRM data.",
        "permissions": [
            # Operations
            ("operations", "routes", "view"), ("operations", "routes", "create"),
            ("operations", "routes", "edit"), ("operations", "routes", "cancel"),
            ("operations", "bookings", "view"), ("operations", "bookings", "create"),
            ("operations", "bookings", "edit"), ("operations", "bookings", "cancel"),
            ("operations", "dispatch", "view"), ("operations", "dispatch", "assign"),
            ("operations", "duties", "view"), ("operations", "duties", "edit"),
            # Fleet
            ("fleet", "vehicles", "view"), ("fleet", "vehicles", "create"), ("fleet", "vehicles", "edit"),
            ("fleet", "drivers", "view"), ("fleet", "drivers", "create"), ("fleet", "drivers", "edit"),
            # CRM
            ("crm", "clients", "view"), ("crm", "vendors", "view"), ("crm", "operating_units", "view"),
            # Reports
            ("reports", "operations", "view"), ("reports", "operations", "export"),
        ],
    },
    {
        "code": "dispatcher",
        "name": "Dispatcher",
        "description": "Can manage dispatch and duties. Read-only access to bookings and fleet.",
        "permissions": [
            ("operations", "bookings", "view"),
            ("operations", "dispatch", "view"), ("operations", "dispatch", "assign"),
            ("operations", "duties", "view"), ("operations", "duties", "edit"),
            ("fleet", "vehicles", "view"),
            ("fleet", "drivers", "view"),
        ],
    },
    {
        "code": "finance_manager",
        "name": "Finance Manager",
        "description": "Full access to finance modules: billing, vendor payments, invoices, P&L.",
        "permissions": [
            ("finance", "billing", "view"), ("finance", "billing", "generate"),
            ("finance", "vendor_payments", "view"), ("finance", "vendor_payments", "process"),
            ("reports", "finance", "view"), ("reports", "finance", "export"),
            # Read-only CRM for context
            ("crm", "clients", "view"), ("crm", "vendors", "view"),
        ],
    },
    {
        "code": "fleet_manager",
        "name": "Fleet Manager",
        "description": "Full control over vehicles and drivers. Read-only operations access.",
        "permissions": [
            ("fleet", "vehicles", "view"), ("fleet", "vehicles", "create"), ("fleet", "vehicles", "edit"),
            ("fleet", "drivers", "view"), ("fleet", "drivers", "create"), ("fleet", "drivers", "edit"),
            ("operations", "duties", "view"),
        ],
    },
    {
        "code": "reporting_user",
        "name": "Reporting User",
        "description": "Read-only access to all reports and dashboards. No operational capabilities.",
        "permissions": [
            ("reports", "operations", "view"), ("reports", "operations", "export"),
            ("reports", "finance", "view"), ("reports", "finance", "export"),
            ("operations", "bookings", "view"),
        ],
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        for tpl_data in PLATFORM_TEMPLATES:
            # Check if already exists
            from sqlalchemy import select
            stmt = select(PlatformRoleTemplate).where(PlatformRoleTemplate.code == tpl_data["code"])
            existing = (await db.execute(stmt)).scalar_one_or_none()
            if existing:
                print(f"  Skipping '{tpl_data['code']}' (already exists)")
                continue

            tpl = PlatformRoleTemplate(
                id=uuid.uuid4(),
                code=tpl_data["code"],
                name=tpl_data["name"],
                description=tpl_data["description"],
                version=1,
                is_active=True,
            )
            db.add(tpl)
            await db.flush()

            for mod, page, action in tpl_data["permissions"]:
                db.add(PlatformRoleTemplatePermission(
                    id=uuid.uuid4(),
                    template_id=tpl.id,
                    module_code=mod,
                    page_code=page,
                    action_code=action,
                ))

            print(f"  Created template: {tpl_data['name']}")

        await db.commit()
        print("Platform templates seeded.")


if __name__ == "__main__":
    asyncio.run(seed())
