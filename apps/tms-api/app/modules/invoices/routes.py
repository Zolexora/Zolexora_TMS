import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.auth.dependencies import get_current_user, get_current_active_organisation, AuthenticatedUser
from app.modules.invoices.schemas import InvoiceCreateRequest, InvoiceResponse
from app.modules.invoices.models import Invoice, InvoiceLine, InvoiceTaxLine, InvoiceStatus
from app.modules.billing.models import BillingRecord, BillingStatus, FinancialSnapshot, FinancialSnapshotLine
import datetime

from fastapi import BackgroundTasks
from app.modules.invoices.pdf_service import generate_invoice_pdf_bytes
from app.core.storage import upload_document_to_r2
from app.modules.customers.models import Customer


router = APIRouter(prefix="/invoices", tags=["Invoices"])

def _generate_invoice_number(db) -> str:
    # In a real app, use a sequence or robust generator. Using UUID prefix for simplicity.
    return f"INV-{uuid.uuid4().hex[:8].upper()}"


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    request: InvoiceCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Generate a DRAFT invoice from one or more pending BillingRecords.
    """
    if not request.billing_record_ids:
        raise HTTPException(status_code=400, detail="At least one billing record must be provided")

    # Fetch billing records
    br_query = await db.execute(
        select(BillingRecord)
        .options(
            selectinload(BillingRecord.snapshot).selectinload(FinancialSnapshot.lines)
        )
        .where(
            BillingRecord.id.in_(request.billing_record_ids),
            BillingRecord.organisation_id == current_org_user.organisation_id,
            BillingRecord.customer_id == request.customer_id
        )
    )
    records = br_query.scalars().all()
    
    if len(records) != len(request.billing_record_ids):
        raise HTTPException(status_code=400, detail="One or more billing records not found or belong to a different customer/org")
        
    for r in records:
        if r.status != BillingStatus.PENDING:
            raise HTTPException(status_code=400, detail=f"Billing record {r.id} is not PENDING")
        if not r.snapshot:
            raise HTTPException(status_code=400, detail=f"Billing record {r.id} has no snapshot")

    # Aggregate snapshots into an Invoice
    invoice = Invoice(
        organisation_id=current_org_user.organisation_id,
        customer_id=request.customer_id,
        invoice_number=_generate_invoice_number(db),
        invoice_date=request.invoice_date,
        due_date=request.due_date,
        notes=request.notes,
        terms=request.terms,
        status=InvoiceStatus.DRAFT,
        created_by_user_id=current_user.id
    )
    
    # We will compute these as we add lines
    subtotal = 0
    taxable_amount = 0
    tax_amount = 0
    discount_amount = 0
    grand_total = 0
    
    invoice_lines = []
    
    for r in records:
        snap: FinancialSnapshot = r.snapshot
        subtotal += snap.subtotal
        taxable_amount += snap.taxable_amount
        tax_amount += snap.tax_amount
        discount_amount += snap.discount_amount
        grand_total += snap.grand_total
        
        # We add lines to the invoice
        for s_line in snap.lines:
            # We skip adding tax lines as standard invoice lines if we separate them, but keeping it simple:
            if not s_line.is_tax:
                il = InvoiceLine(
                    billing_record_id=r.id,
                    description=s_line.description,
                    quantity=s_line.quantity,
                    unit=s_line.unit,
                    unit_rate=s_line.unit_rate,
                    amount=s_line.amount
                )
                invoice_lines.append(il)
                
    invoice.subtotal = subtotal
    invoice.taxable_amount = taxable_amount
    invoice.tax_amount = tax_amount
    invoice.discount_amount = discount_amount
    invoice.grand_total = grand_total
    invoice.amount_due = grand_total
    
    invoice.lines = invoice_lines
    db.add(invoice)
    
    # Update billing records
    for r in records:
        r.status = BillingStatus.INVOICED
        r.invoice_id = invoice.id
        
    await db.commit()
    await db.refresh(invoice)
    
    return invoice


@router.get("", response_model=List[InvoiceResponse])
async def list_invoices(
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Invoice)
        .where(Invoice.organisation_id == current_org_user.organisation_id)
        .order_by(Invoice.created_at.desc())
    )
    return query.scalars().all()


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.lines), selectinload(Invoice.tax_lines))
        .where(Invoice.id == invoice_id, Invoice.organisation_id == current_org_user.organisation_id)
    )
    invoice = query.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/{invoice_id}/finalize")
async def finalize_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.organisation_id == current_org_user.organisation_id)
    )
    invoice = query.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if invoice.status != InvoiceStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only DRAFT invoices can be finalized")
        
    invoice.status = InvoiceStatus.FINALIZED
    invoice.finalized_at = datetime.datetime.now(datetime.timezone.utc)
    
    # Lock snapshots (if not already locked)
    br_query = await db.execute(select(BillingRecord).where(BillingRecord.invoice_id == invoice.id))
    for br in br_query.scalars().all():
        if br.snapshot_id:
            snap_query = await db.execute(select(FinancialSnapshot).where(FinancialSnapshot.id == br.snapshot_id))
            snap = snap_query.scalar_one_or_none()
            if snap:
                snap.is_finalized = True
                
    await db.commit()
    return {"message": "Invoice finalized successfully"}


@router.post("/{invoice_id}/pdf")
async def generate_invoice_pdf(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Invoice).options(selectinload(Invoice.lines), selectinload(Invoice.tax_lines))
        .where(Invoice.id == invoice_id, Invoice.organisation_id == current_org_user.organisation_id)
    )
    invoice = query.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if invoice.status == InvoiceStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Cannot generate PDF for DRAFT invoice")
        
    if invoice.pdf_url:
        return {"pdf_url": invoice.pdf_url}
        
    # Get organization and customer details
    from app.modules.organisations.models import Organisation
    org_query = await db.execute(select(Organisation).where(Organisation.id == current_org_user.organisation_id))
    org = org_query.scalar_one_or_none()
    
    cust_query = await db.execute(select(Customer).where(Customer.id == invoice.customer_id))
    customer = cust_query.scalar_one_or_none()
    
    pdf_bytes = generate_invoice_pdf_bytes(invoice, org, customer)
    
    filename = f"{invoice.invoice_number}.pdf"
    folder = f"zolexora/{current_org_user.organisation_id}/invoices"
    
    # Upload to R2
    pdf_url = await upload_document_to_r2(
        file_bytes=pdf_bytes,
        filename=filename,
        content_type="application/pdf",
        folder=folder,
        org_id=current_org_user.organisation_id
    )
    
    invoice.pdf_url = pdf_url
    await db.commit()
    return {"pdf_url": invoice.pdf_url}


@router.post("/{invoice_id}/cancel")
async def cancel_invoice(
    invoice_id: uuid.UUID,
    reason: str,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.organisation_id == current_org_user.organisation_id)
    )
    invoice = query.scalar_one_or_none()
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if invoice.status == InvoiceStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Invoice is already cancelled")
        
    invoice.status = InvoiceStatus.CANCELLED
    invoice.cancellation_reason = reason
    
    # Also unlock the financial snapshots
    br_query = await db.execute(select(BillingRecord).where(BillingRecord.invoice_id == invoice.id))
    for br in br_query.scalars().all():
        if br.snapshot_id:
            snap_query = await db.execute(select(FinancialSnapshot).where(FinancialSnapshot.id == br.snapshot_id))
            snap = snap_query.scalar_one_or_none()
            if snap:
                snap.is_finalized = False
        # Optional: unlink the billing record or set its status back to PENDING?
        br.status = BillingStatus.PENDING
        br.invoice_id = None
        
    await db.commit()
    return {"message": "Invoice cancelled successfully"}

@router.get("/reports/receivables-ageing")
async def get_receivables_ageing(
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    """
    Calculate Receivables Ageing Buckets for outstanding invoices.
    Buckets: Current, 1-30 days, 31-60 days, 61-90 days, >90 days overdue.
    """
    query = await db.execute(
        select(Invoice).where(
            Invoice.organisation_id == current_org_user.organisation_id,
            Invoice.status.in_([InvoiceStatus.FINALIZED, InvoiceStatus.PARTIALLY_PAID])
        )
    )
    invoices = query.scalars().all()
    
    today = datetime.date.today()
    
    buckets = {
        "current": Decimal("0.0"),
        "1_30_days": Decimal("0.0"),
        "31_60_days": Decimal("0.0"),
        "61_90_days": Decimal("0.0"),
        "over_90_days": Decimal("0.0"),
        "total_outstanding": Decimal("0.0")
    }
    
    for inv in invoices:
        due_amount = inv.amount_due
        if due_amount <= 0:
            continue
            
        buckets["total_outstanding"] += due_amount
        
        days_overdue = (today - inv.due_date).days
        
        if days_overdue <= 0:
            buckets["current"] += due_amount
        elif 1 <= days_overdue <= 30:
            buckets["1_30_days"] += due_amount
        elif 31 <= days_overdue <= 60:
            buckets["31_60_days"] += due_amount
        elif 61 <= days_overdue <= 90:
            buckets["61_90_days"] += due_amount
        else:
            buckets["over_90_days"] += due_amount
            
    return buckets
