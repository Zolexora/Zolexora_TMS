import datetime
import enum
import uuid
from decimal import Decimal
from sqlalchemy import Boolean, UniqueConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class InvoiceStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    FINALIZED = "FINALIZED"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    VOID = "VOID"


class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    
    invoice_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    invoice_date: Mapped[datetime.date] = mapped_column(DateTime(timezone=True), nullable=False)
    due_date: Mapped[datetime.date] = mapped_column(DateTime(timezone=True), nullable=False)
    billing_period_start: Mapped[datetime.date | None] = mapped_column(DateTime(timezone=True), nullable=True)
    billing_period_end: Mapped[datetime.date | None] = mapped_column(DateTime(timezone=True), nullable=True)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus, name="invoice_status", create_type=False), default=InvoiceStatus.DRAFT, nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    finalized_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin")
    tax_lines = relationship("InvoiceTaxLine", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin")


class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    billing_record_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("billing_records.id", ondelete="SET NULL"), nullable=True
    )
    
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1.0"), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    unit_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    
    invoice = relationship("Invoice", back_populates="lines")


class InvoiceTaxLine(Base):
    __tablename__ = "invoice_tax_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    tax_name: Mapped[str] = mapped_column(String(64), nullable=False) # e.g. CGST, SGST, IGST
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    invoice = relationship("Invoice", back_populates="tax_lines")

class NoteType(str, enum.Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"

class NoteStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    FINALIZED = "FINALIZED"
    CANCELLED = "CANCELLED"

class FinancialAdjustmentNote(Base, TimestampMixin):
    __tablename__ = "financial_adjustment_notes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    note_type: Mapped[NoteType] = mapped_column(Enum(NoteType, name="adjustment_note_type"), nullable=False)
    note_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    note_date: Mapped[datetime.date] = mapped_column(DateTime(timezone=True), nullable=False)
    
    reason: Mapped[str] = mapped_column(String(512), nullable=False)
    
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    
    status: Mapped[NoteStatus] = mapped_column(Enum(NoteStatus, name="adjustment_note_status"), default=NoteStatus.DRAFT, nullable=False)
    pdf_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    finalized_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    lines = relationship("FinancialAdjustmentNoteLine", back_populates="note", cascade="all, delete-orphan", lazy="selectin")
    tax_lines = relationship("FinancialAdjustmentNoteTaxLine", back_populates="note", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organisation_id", "note_type", "note_number", name="uq_adjustment_note_num"),
    )

class FinancialAdjustmentNoteLine(Base):
    __tablename__ = "financial_adjustment_note_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("financial_adjustment_notes.id", ondelete="CASCADE"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    note = relationship("FinancialAdjustmentNote", back_populates="lines")

class FinancialAdjustmentNoteTaxLine(Base):
    __tablename__ = "financial_adjustment_note_tax_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    note_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("financial_adjustment_notes.id", ondelete="CASCADE"), nullable=False, index=True)
    tax_name: Mapped[str] = mapped_column(String(64), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    
    note = relationship("FinancialAdjustmentNote", back_populates="tax_lines")
