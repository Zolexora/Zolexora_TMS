import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.auth.dependencies import get_current_user, get_current_active_organisation, AuthenticatedUser
from app.modules.expenses.schemas import ExpenseCreateRequest, ExpenseResponse
from app.modules.expenses.models import Expense, ExpenseCategory

router = APIRouter(prefix="/expenses", tags=["Expenses"])

@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    request: ExpenseCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        category_enum = ExpenseCategory(request.category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid expense category: {request.category}")
        
    expense = Expense(
        organisation_id=current_org_user.organisation_id,
        duty_id=request.duty_id,
        trip_id=request.trip_id,
        vehicle_id=request.vehicle_id,
        driver_id=request.driver_id,
        category=category_enum,
        amount=request.amount,
        currency=request.currency,
        expense_date=request.expense_date,
        attachment_url=request.attachment_url,
        notes=request.notes,
        created_by_user_id=current_user.id
    )
    
    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    
    return expense

@router.get("", response_model=List[ExpenseResponse])
async def list_expenses(
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Expense)
        .where(Expense.organisation_id == current_org_user.organisation_id)
        .order_by(Expense.expense_date.desc())
    )
    return query.scalars().all()

@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_org_user: AuthenticatedUser = Depends(get_current_active_organisation),
):
    query = await db.execute(
        select(Expense)
        .where(Expense.id == expense_id, Expense.organisation_id == current_org_user.organisation_id)
    )
    expense = query.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return expense
