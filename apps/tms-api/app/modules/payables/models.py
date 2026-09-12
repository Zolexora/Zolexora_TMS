import datetime
import enum
import uuid
from decimal import Decimal
from sqlalchemy import Boolean, UniqueConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class PayableStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"


class Payable(Base, TimestampMixin):
    __tablename__ = "payables"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    
    reference_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    duty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("duties.id", ondelete="SET NULL"), nullable=True
    )
    
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    advances: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    
    status: Mapped[PayableStatus] = mapped_column(Enum(PayableStatus, name="payable_status", create_type=False), default=PayableStatus.DRAFT, nullable=False)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    lines = relationship("PayableLine", back_populates="payable", cascade="all, delete-orphan", lazy="selectin")
    settlements = relationship("Settlement", back_populates="payable", cascade="all, delete-orphan", lazy="selectin")


class PayableLine(Base):
    __tablename__ = "payable_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payables.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_deduction: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    payable = relationship("Payable", back_populates="lines")


class Settlement(Base, TimestampMixin):
    __tablename__ = "settlements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payables.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    settlement_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payment_reference: Mapped[str | None] = mapped_column(String(128), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    
    payable = relationship("Payable", back_populates="settlements")

class VendorSettlementStatement(Base, TimestampMixin):
    __tablename__ = "vendor_settlement_statements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vendors.id", ondelete="RESTRICT"), nullable=True, index=True)
    driver_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("drivers.id", ondelete="RESTRICT"), nullable=True, index=True)
    
    statement_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    statement_date: Mapped[datetime.date] = mapped_column(DateTime(timezone=True), nullable=False)
    
    period_start: Mapped[datetime.date | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime.date | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    gross_payable: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    total_advances: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    net_payable: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    
    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("organisation_id", "statement_number", name="uq_vendor_settlement_num"),
    )
