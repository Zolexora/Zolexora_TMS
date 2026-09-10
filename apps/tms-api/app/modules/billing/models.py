import datetime
import enum
import uuid
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class RateCard(Base, TimestampMixin):
    __tablename__ = "rate_cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    booking_type: Mapped[str] = mapped_column(String(64), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    versions = relationship("RateCardVersion", back_populates="rate_card", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        CheckConstraint("length(trim(name)) between 2 and 160", name="ck_rate_card_name_len"),
    )


class RateCardVersion(Base):
    __tablename__ = "rate_card_versions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rate_cards.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_immutable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False
    )
    effective_to: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rate_card = relationship("RateCard", back_populates="versions")
    rules = relationship("RateCardRule", back_populates="rate_card_version", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("rate_card_id", "version_number", name="uq_rate_card_version"),
    )


class RateRuleType(str, enum.Enum):
    FIXED_TRIP = "FIXED_TRIP"
    PER_KM = "PER_KM"
    PER_HOUR = "PER_HOUR"
    MINIMUM_CHARGE = "MINIMUM_CHARGE"
    EXTRA_KM = "EXTRA_KM"
    EXTRA_HOUR = "EXTRA_HOUR"
    WAITING_CHARGE = "WAITING_CHARGE"
    NIGHT_SURCHARGE = "NIGHT_SURCHARGE"
    AIRPORT_SURCHARGE = "AIRPORT_SURCHARGE"
    TOLL = "TOLL"
    PARKING = "PARKING"
    DRIVER_ALLOWANCE = "DRIVER_ALLOWANCE"
    ADDITIONAL_STOP = "ADDITIONAL_STOP"
    CANCELLATION_FEE = "CANCELLATION_FEE"
    PERCENTAGE_SURCHARGE = "PERCENTAGE_SURCHARGE"
    PERCENTAGE_DISCOUNT = "PERCENTAGE_DISCOUNT"
    TAX_CGST = "TAX_CGST"
    TAX_SGST = "TAX_SGST"
    TAX_IGST = "TAX_IGST"
    CUSTOM_ADJUSTMENT = "CUSTOM_ADJUSTMENT"


class RateCardRule(Base):
    __tablename__ = "rate_card_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_card_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rate_card_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_type: Mapped[RateRuleType] = mapped_column(Enum(RateRuleType, name="rate_rule_type", create_type=False), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Financial fields
    base_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"), nullable=False)
    quantity_included: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"), nullable=False)
    rate_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"), nullable=False)
    is_percentage: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    percentage_value: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.0"), nullable=False)
    
    sequence: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    conditions: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    rate_card_version = relationship("RateCardVersion", back_populates="rules")


class FinancialSnapshot(Base, TimestampMixin):
    __tablename__ = "financial_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bookings.id", ondelete="SET NULL"), nullable=True
    )
    duty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("duties.id", ondelete="SET NULL"), nullable=True, index=True
    )
    trip_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trips.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rate_card_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rate_card_versions.id", ondelete="RESTRICT"), nullable=True
    )

    operational_inputs: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    surcharge_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    grand_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    lines = relationship("FinancialSnapshotLine", back_populates="snapshot", cascade="all, delete-orphan", lazy="selectin")


class FinancialSnapshotLine(Base):
    __tablename__ = "financial_snapshot_lines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("financial_snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    rule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rate_card_rules.id", ondelete="SET NULL"), nullable=True
    )
    
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_type: Mapped[str] = mapped_column(String(64), nullable=False)
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1.0"), nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    unit_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    is_tax: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    snapshot = relationship("FinancialSnapshot", back_populates="lines")


class BillingStatus(str, enum.Enum):
    ELIGIBLE = "ELIGIBLE"
    PENDING = "PENDING"
    INVOICED = "INVOICED"
    CANCELLED = "CANCELLED"

class BillingRecord(Base, TimestampMixin):
    __tablename__ = "billing_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    duty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("duties.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("financial_snapshots.id", ondelete="RESTRICT"), nullable=True
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    ) # Soft link to avoid circular dependencies during generation
    
    status: Mapped[BillingStatus] = mapped_column(Enum(BillingStatus, name="billing_status", create_type=False), default=BillingStatus.ELIGIBLE, nullable=False)

    __table_args__ = (
        UniqueConstraint("duty_id", name="uq_billing_duty"),
    )
