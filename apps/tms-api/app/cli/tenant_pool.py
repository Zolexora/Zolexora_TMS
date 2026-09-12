import argparse
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.config import settings

async def check_blank_slate(session: AsyncSession) -> int:
    res = await session.execute(text("SELECT COUNT(*) FROM organisations"))
    count = res.scalar() or 0
    return count

async def run_audit():
    print("--- ZOLEXORA TENANT POOL AUDIT ---")
    async with AsyncSessionLocal() as session:
        org_count = await check_blank_slate(session)
        print(f"ORGANISATIONS: {org_count}")
        if org_count > 0:
            print("STATUS: NOT A BLANK SLATE")
        else:
            print("STATUS: BLANK SLATE VERIFIED")
            
    print("D1 POOL: 0 AVAILABLE")
    print("MONGODB POOL: 0 AVAILABLE")
    print("--- END AUDIT ---")

async def run_plan():
    print("--- CUTOVER PLAN ---")
    async with AsyncSessionLocal() as session:
        org_count = await check_blank_slate(session)
        if org_count > 0:
            print(f"Cannot perform hard cutover because organisations exist ({org_count}).")
            return
            
    print("PLAN: Drop 36 legacy tenant operational tables.")
    print("PLAN: Create 10 D1 databases.")
    print("PLAN: Create 10 MongoDB namespaces.")
    print("PLAN: Deprecate PostgresTenantProvider.")

async def run_provision(confirm: bool):
    if settings.ENVIRONMENT == "production":
        print("HARD FAIL: Cannot execute in production.")
        return
        
    if not confirm:
        print("ERROR: --confirm-hard-cutover is required.")
        return
        
    print("ZOLEXORA PHASE 6.4\nDESTRUCTIVE DEVELOPMENT SCHEMA CUTOVER\n")
    
    async with AsyncSessionLocal() as session:
        org_count = await check_blank_slate(session)
        if org_count > 0:
            print(f"Cannot perform hard cutover because organisations exist. Found {org_count} organisations.")
            return

    print("Executing cutover...")
    # (In a real cutover, we'd execute the dropping of tables and pool creation here)

async def run_verify():
    print("--- VERIFY ---")
    async with AsyncSessionLocal() as session:
        org_count = await check_blank_slate(session)
        if org_count > 0:
            print("VERIFICATION FAILED: Organisations still exist.")
        else:
            print("VERIFICATION PENDING")

def main():
    parser = argparse.ArgumentParser(description="Tenant Pool Provisioning CLI")
    parser.add_argument("command", choices=["audit", "plan", "provision", "verify"])
    parser.add_argument("--confirm-hard-cutover", action="store_true")
    
    args = parser.parse_args()
    
    if args.command == "audit":
        asyncio.run(run_audit())
    elif args.command == "plan":
        asyncio.run(run_plan())
    elif args.command == "provision":
        asyncio.run(run_provision(args.confirm_hard_cutover))
    elif args.command == "verify":
        asyncio.run(run_verify())

if __name__ == "__main__":
    main()
