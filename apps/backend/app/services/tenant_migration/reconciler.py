from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

class TenantDataReconciler:
    def __init__(self, pg_db: AsyncSession, importer, org_id: str):
        self.pg_db = pg_db
        self.importer = importer
        self.org_id = org_id

    async def reconcile(self, tables: List[str]) -> Dict[str, Any]:
        result = {
            "tables": {},
            "counts_match": True,
            "financials_match": True,
            "details": []
        }
        
        for table in tables:
            # PG count
            pg_query = text(f"SELECT COUNT(*) FROM public.{table} WHERE organisation_id = :org_id")
            pg_res = await self.pg_db.execute(pg_query, {"org_id": self.org_id})
            pg_count = pg_res.scalar()
            
            # D1/SQLite count
            with self.importer.engine.connect() as conn:
                sqlite_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                
            matches = (pg_count == sqlite_count)
            if not matches:
                result["counts_match"] = False
                result["details"].append(f"Count mismatch in {table}: PG={pg_count}, D1={sqlite_count}")
                
            result["tables"][table] = {
                "source_count": pg_count,
                "dest_count": sqlite_count,
                "matches": matches
            }
            
            # Financial check for specific tables
            if table == "invoices":
                # PG Sum
                pg_sum_q = text(f"SELECT SUM(grand_total) FROM public.invoices WHERE organisation_id = :org_id")
                pg_sum = (await self.pg_db.execute(pg_sum_q, {"org_id": self.org_id})).scalar() or 0
                
                # D1 sum
                with self.importer.engine.connect() as conn:
                    # D1 stores exact decimal as string, sum might not work perfectly directly in SQL, we fetch and sum in Python
                    d1_rows = conn.execute(text(f"SELECT grand_total FROM invoices")).fetchall()
                    # Convert string to decimal, avoiding floating point
                    d1_sum = sum(Decimal(row[0]) for row in d1_rows if row[0] is not None)
                    
                if Decimal(str(pg_sum)) != d1_sum:
                    result["financials_match"] = False
                    result["details"].append(f"Financial mismatch in invoices: PG={pg_sum}, D1={d1_sum}")

        return result
