from fastapi import APIRouter, Depends, HTTPException
import uuid
from typing import List, Dict, Any
from app.auth.dependencies import get_tenant_context, AuthenticatedUser, get_current_active_organisation
from app.core.tenant import TenantContext
from pydantic import BaseModel

router = APIRouter(tags=["Billing"], prefix="/api/v1")

@router.get("/rate-cards")
async def list_rate_cards(
    ctx: TenantContext = Depends(get_tenant_context)
):
    conn = await ctx.d1.get_connection()
    
    # Query rate cards and their versions/rules
    async with conn.execute(
        """
        SELECT 
            rc.id, rc.customer_id, rc.vendor_id, rc.vehicle_type, rc.created_at, rc.updated_at,
            c.name as customer_name, v.name as vendor_name
        FROM rate_cards rc
        LEFT JOIN customers c ON c.id = rc.customer_id
        LEFT JOIN vendors v ON v.id = rc.vendor_id
        """
    ) as cursor:
        rows = await cursor.fetchall()
        
    results = []
    for row in rows:
        rc_id = row["id"]
        
        # Fetch versions
        async with conn.execute(
            "SELECT * FROM rate_card_versions WHERE rate_card_id = ?", (rc_id,)
        ) as v_cursor:
            v_rows = await v_cursor.fetchall()
            
        versions = []
        for v_row in v_rows:
            v_id = v_row["id"]
            # Fetch rules
            async with conn.execute(
                "SELECT * FROM rate_card_rules WHERE rate_card_version_id = ?", (v_id,)
            ) as r_cursor:
                r_rows = await r_cursor.fetchall()
                
            versions.append({
                "id": v_row["id"],
                "version_number": v_row["version_number"],
                "effective_from": v_row["effective_from"],
                "base_rate": v_row["base_rate"],
                "status": v_row["status"],
                "rules": [dict(r) for r in r_rows]
            })
            
        results.append({
            "id": row["id"],
            "customer_id": row["customer_id"],
            "vendor_id": row["vendor_id"],
            "vehicle_type": row["vehicle_type"],
            "name": f"{row['customer_name'] or row['vendor_name'] or 'General'} Rate Card" + (f" - {row['vehicle_type']}" if row['vehicle_type'] else ""),
            "is_active": any(v.get("status") == "ACTIVE" for v in versions),
            "rules": versions[0]["rules"] if versions else [],
            "customer_name": row["customer_name"],
            "vendor_name": row["vendor_name"],
            "created_at": row["created_at"],
            "versions": versions
        })
        
    return results

class RuleUpdate(BaseModel):
    id: str
    rate: float

class RateCardRulesUpdate(BaseModel):
    rules: List[RuleUpdate]

@router.put("/rate-cards/{rate_card_id}/rules")
async def update_rate_card_rules(
    rate_card_id: str,
    payload: RateCardRulesUpdate,
    ctx: TenantContext = Depends(get_tenant_context)
):
    conn = await ctx.d1.get_connection()
    
    # Update each rule
    for rule in payload.rules:
        await conn.execute(
            "UPDATE rate_card_rules SET rate = ? WHERE id = ? AND rate_card_version_id IN (SELECT id FROM rate_card_versions WHERE rate_card_id = ?)",
            (rule.rate, rule.id, rate_card_id)
        )
        
    return {"status": "success"}
