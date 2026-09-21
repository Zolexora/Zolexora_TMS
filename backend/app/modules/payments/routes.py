import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.auth.dependencies import get_current_user, get_current_active_organisation, AuthenticatedUser
from app.modules.payments.schemas import PaymentCreateRequest, PaymentResponse
from app.modules.payments.models import Payment, PaymentAllocation, PaymentStatus
from app.modules.invoices.models import Invoice, InvoiceStatus

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: PaymentCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """
    Record an incoming payment and allocate it against one or more invoices.
    """
    total_allocated = sum(alloc.amount_allocated for alloc in request.allocations)
    if total_allocated > request.amount:
        raise HTTPException(status_code=400, detail="Total allocated amount cannot exceed payment amount")
        
    payment = Payment(
        organisation_id=current_org_user.organisation_id,
        customer_id=request.customer_id,
        provider=request.provider,
        provider_transaction_id=request.provider_transaction_id,
        payment_method=request.payment_method,
        amount=request.amount,
        unallocated_amount=request.amount - total_allocated,
        currency=request.currency,
        payment_date=request.payment_date,
        status=PaymentStatus.SUCCESS, # Assume success for manual entry
        notes=request.notes,
        metadata_dict={},
        created_by_user_id=current_user.id
    )
    db.add(payment)
    await db.flush() # Get payment.id
    
    allocations_db = []
    
    # Process allocations and update invoices
    for alloc in request.allocations:
        inv_query = await db.execute(
            select(Invoice).where(
                Invoice.id == alloc.invoice_id,
                Invoice.organisation_id == current_org_user.organisation_id
            )
        )
        invoice = inv_query.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=404, detail=f"Invoice {alloc.invoice_id} not found")
            
        if invoice.status not in [InvoiceStatus.FINALIZED, InvoiceStatus.PARTIALLY_PAID]:
            raise HTTPException(status_code=400, detail=f"Cannot allocate payment to invoice {invoice.id} because it is {invoice.status}")
            
        if alloc.amount_allocated > invoice.amount_due:
            raise HTTPException(status_code=400, detail=f"Allocation ({alloc.amount_allocated}) exceeds amount due ({invoice.amount_due}) for invoice {invoice.id}")
            
        pa = PaymentAllocation(
            payment_id=payment.id,
            invoice_id=invoice.id,
            amount_allocated=alloc.amount_allocated
        )
        allocations_db.append(pa)
        db.add(pa)
        
        invoice.amount_paid += alloc.amount_allocated
        invoice.amount_due -= alloc.amount_allocated
        
        if invoice.amount_due == 0:
            invoice.status = InvoiceStatus.PAID
        elif invoice.amount_paid > 0:
            invoice.status = InvoiceStatus.PARTIALLY_PAID
            
    payment.allocations = allocations_db
    await db.commit()
    await db.refresh(payment)
    return payment

@router.get("", response_model=List[PaymentResponse])
async def list_payments(
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Payment)
        .options(selectinload(Payment.allocations))
        .where(Payment.organisation_id == current_org_user.organisation_id)
        .order_by(Payment.created_at.desc())
    )
    return query.scalars().all()

@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Payment)
        .options(selectinload(Payment.allocations))
        .where(Payment.id == payment_id, Payment.organisation_id == current_org_user.organisation_id)
    )
    payment = query.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

import csv
import io
import datetime
from fastapi import UploadFile, File

@router.post("/reconcile-statement")
async def reconcile_bank_statement(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    """
    Upload a CSV bank statement to automatically reconcile payments.
    Expected CSV columns: date, amount, reference_number
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    
    matched_count = 0
    unmatched_count = 0
    errors = []
    
    for row_idx, row in enumerate(reader, start=2):
        ref_num = row.get("reference_number", "").strip()
        if not ref_num:
            unmatched_count += 1
            errors.append(f"Row {row_idx}: Missing reference_number")
            continue
            
        # Try to find a matching payment that isn't reconciled yet
        query = await db.execute(
            select(Payment)
            .where(
                Payment.provider_transaction_id == ref_num,
                Payment.organisation_id == current_org_user.organisation_id,
                Payment.reconciled_at.is_(None)
            )
        )
        payment = query.scalar_one_or_none()
        
        if payment:
            # We found a match, reconcile it
            payment.reconciled_at = datetime.datetime.now(datetime.timezone.utc)
            matched_count += 1
        else:
            unmatched_count += 1
            errors.append(f"Row {row_idx}: No pending payment found for reference {ref_num}")
            
    await db.commit()
    
    return {
        "status": "success",
        "message": "Bank statement processed",
        "matched_payments": matched_count,
        "unmatched_rows": unmatched_count,
        "errors": errors[:10] # Return up to 10 errors for brevity
    }

