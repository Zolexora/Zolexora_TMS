import datetime
import enum
import uuid
from decimal import Decimal
from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class ExpenseCategory(str, enum.Enum):
    FUEL = "FUEL"
    TOLL = "TOLL"
    PARKING = "PARKING"
    MAINTENANCE = "MAINTENANCE"
    DRIVER_ALLOWANCE = "DRIVER_ALLOWANCE"
    FOOD = "FOOD"
    MISCELLANEOUS = "MISCELLANEOUS"


class Expense(Base, TimestampMixin):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    duty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("duties.id", ondelete="SET NULL"), nullable=True, index=True
    )
    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    category: Mapped[ExpenseCategory] = mapped_column(Enum(ExpenseCategory, name="expense_category", create_type=False), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    expense_date: Mapped[datetime.date] = mapped_column(DateTime(timezone=True), nullable=False)
    
    attachment_url: Mapped[str | None] = mapped_column(String(512), nullable=True) # R2 URL
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
