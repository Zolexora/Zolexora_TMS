import uuid
import datetime
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.auth.dependencies import get_current_user, get_current_active_organisation, AuthenticatedUser
from app.modules.invoices.models import FinancialAdjustmentNote, FinancialAdjustmentNoteLine, FinancialAdjustmentNoteTaxLine, NoteStatus, NoteType, Invoice
from app.modules.invoices.adjustment_schemas import AdjustmentNoteCreateRequest, AdjustmentNoteResponse

router = APIRouter(prefix="/adjustments", tags=["Adjustments"])

def _generate_note_number(note_type: NoteType) -> str:
    prefix = "CN" if note_type == NoteType.CREDIT else "DN"
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

@router.post("", response_model=AdjustmentNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_adjustment_note(
    request: AdjustmentNoteCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    # Verify invoice
    invoice_query = await db.execute(
        select(Invoice).where(
            Invoice.id == request.invoice_id, 
            Invoice.organisation_id == current_org_user.organisation_id
        )
    )
    invoice = invoice_query.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    note = FinancialAdjustmentNote(
        organisation_id=current_org_user.organisation_id,
        customer_id=request.customer_id,
        invoice_id=request.invoice_id,
        note_type=request.note_type,
        note_number=_generate_note_number(request.note_type),
        note_date=request.note_date,
        reason=request.reason,
        status=NoteStatus.FINALIZED,  # Auto-finalize for simplicity, but could be DRAFT
        created_by_user_id=current_user.id,
        finalized_at=datetime.datetime.now(datetime.timezone.utc)
    )
    
    subtotal = Decimal("0.0")
    for l in request.lines:
        subtotal += l.amount
        note.lines.append(FinancialAdjustmentNoteLine(description=l.description, amount=l.amount))
        
    tax_amount = Decimal("0.0")
    for tl in request.tax_lines:
        tax_amount += tl.tax_amount
        note.tax_lines.append(FinancialAdjustmentNoteTaxLine(tax_name=tl.tax_name, tax_amount=tl.tax_amount))
        
    note.subtotal = subtotal
    note.tax_amount = tax_amount
    note.grand_total = subtotal + tax_amount
    
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

@router.get("", response_model=List[AdjustmentNoteResponse])
async def list_adjustment_notes(
    note_type: NoteType = None,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    stmt = select(FinancialAdjustmentNote).where(FinancialAdjustmentNote.organisation_id == current_org_user.organisation_id)
    if note_type:
        stmt = stmt.where(FinancialAdjustmentNote.note_type == note_type)
        
    query = await db.execute(stmt.order_by(FinancialAdjustmentNote.created_at.desc()))
    return query.scalars().all()
