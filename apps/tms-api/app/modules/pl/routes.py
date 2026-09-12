import uuid
import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_db
from app.auth.dependencies import get_current_active_organisation, AuthenticatedUser
from app.modules.pl.schemas import PnLSummaryResponse

from app.modules.invoices.models import Invoice, InvoiceStatus
from app.modules.payables.models import Payable, PayableStatus
from app.modules.expenses.models import Expense

router = APIRouter(prefix="/pl", tags=["Profit & Loss"])

def _round(value: float | Decimal | None) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

@router.get("/summary", response_model=PnLSummaryResponse)
async def get_pnl_summary(
    start_date: Optional[datetime.date] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime.date] = Query(None, description="Filter to this date"),
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    """
    Calculate high-level P&L metrics based on recognized financial documents.
    Revenue: FINALIZED, PARTIALLY_PAID, PAID invoices.
    Costs: APPROVED, SETTLED payables + all captured Expenses.
    """
    # 1. Revenue Calculation
    inv_query = select(
        func.sum(Invoice.grand_total).label("gross"),
        func.sum(Invoice.taxable_amount).label("net"),
        func.sum(Invoice.tax_amount).label("taxes")
    ).where(
        Invoice.organisation_id == current_org_user.organisation_id,
        Invoice.status.in_([InvoiceStatus.FINALIZED, InvoiceStatus.PARTIALLY_PAID, InvoiceStatus.PAID])
    )
    
    if start_date:
        inv_query = inv_query.where(Invoice.invoice_date >= start_date)
    if end_date:
        inv_query = inv_query.where(Invoice.invoice_date <= end_date)
        
    inv_res = await db.execute(inv_query)
    inv_row = inv_res.one()
    
    rev_gross = _round(inv_row.gross)
    rev_net = _round(inv_row.net)
    taxes_coll = _round(inv_row.taxes)
    
    # 2. Payables Calculation
    pay_query = select(func.sum(Payable.grand_total)).where(
        Payable.organisation_id == current_org_user.organisation_id,
        Payable.status.in_([PayableStatus.APPROVED, PayableStatus.SETTLED])
    )
    
    if start_date:
        pay_query = pay_query.where(Payable.created_at >= datetime.datetime.combine(start_date, datetime.time.min).replace(tzinfo=datetime.timezone.utc))
    if end_date:
        pay_query = pay_query.where(Payable.created_at <= datetime.datetime.combine(end_date, datetime.time.max).replace(tzinfo=datetime.timezone.utc))
        
    pay_res = await db.execute(pay_query)
    payables_total = _round(pay_res.scalar())
    
    # 3. Expenses Calculation
    exp_query = select(func.sum(Expense.amount)).where(
        Expense.organisation_id == current_org_user.organisation_id
    )
    
    if start_date:
        exp_query = exp_query.where(Expense.expense_date >= start_date)
    if end_date:
        exp_query = exp_query.where(Expense.expense_date <= end_date)
        
    exp_res = await db.execute(exp_query)
    expenses_total = _round(exp_res.scalar())
    
    # Aggregation
    total_direct_costs = payables_total + expenses_total
    gross_profit = rev_net - total_direct_costs
    
    margin_pct = Decimal("0.00")
    if rev_net > 0:
        margin_pct = _round((gross_profit / rev_net) * Decimal("100.0"))
        
    return PnLSummaryResponse(
        organisation_id=str(current_org_user.organisation_id),
        start_date=start_date,
        end_date=end_date,
        total_revenue_gross=rev_gross,
        total_revenue_net=rev_net,
        total_taxes_collected=taxes_coll,
        total_vendor_driver_payables=payables_total,
        total_operational_expenses=expenses_total,
        total_direct_costs=total_direct_costs,
        gross_profit=gross_profit,
        gross_margin_percentage=margin_pct
    )

from app.modules.pl.models import FinancialPeriod, PeriodStatus
from pydantic import BaseModel

class PeriodCreateSchema(BaseModel):
    period_name: str
    start_date: datetime.date
    end_date: datetime.date

@router.post("/periods")
async def create_financial_period(
    req: PeriodCreateSchema,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
    current_user: AuthenticatedUser = Depends(get_current_active_organisation)
):
    period = FinancialPeriod(
        organisation_id=current_org_user.organisation_id,
        period_name=req.period_name,
        start_date=req.start_date,
        end_date=req.end_date,
        status=PeriodStatus.OPEN,
        opened_at=datetime.datetime.now(datetime.timezone.utc)
    )
    db.add(period)
    await db.commit()
    return period

@router.post("/periods/{period_id}/close")
async def close_financial_period(
    period_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
    current_user: AuthenticatedUser = Depends(get_current_active_organisation)
):
    from fastapi import HTTPException
    query = await db.execute(select(FinancialPeriod).where(FinancialPeriod.id == period_id, FinancialPeriod.organisation_id == current_org_user.organisation_id))
    period = query.scalar_one_or_none()
    if not period:
        raise HTTPException(404, "Period not found")
        
    period.status = PeriodStatus.CLOSED
    period.closed_at = datetime.datetime.now(datetime.timezone.utc)
    period.closed_by_user_id = current_user.user_id
    
    await db.commit()
    return {"message": "Period closed"}

@router.get("/periods")
async def list_financial_periods(
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation)
):
    query = await db.execute(select(FinancialPeriod).where(FinancialPeriod.organisation_id == current_org_user.organisation_id).order_by(FinancialPeriod.start_date.desc()))
    return query.scalars().all()
