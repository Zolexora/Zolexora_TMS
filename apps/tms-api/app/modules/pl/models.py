import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class FinancialAuditLog(Base):
    __tablename__ = "financial_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False) # e.g. INVOICE, PAYMENT, PAYABLE
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False) # e.g. CREATED, FINALIZED, CANCELLED
    
    old_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_values: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)

import enum
from sqlalchemy import Boolean, Enum, UniqueConstraint
from app.db.base import TimestampMixin

class PeriodStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class FinancialPeriod(Base, TimestampMixin):
    __tablename__ = "financial_periods"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    period_name: Mapped[str] = mapped_column(String(64), nullable=False) # e.g. "FY2026-Q1" or "2026-09"
    start_date: Mapped[datetime.date] = mapped_column(DateTime(timezone=True), nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(DateTime(timezone=True), nullable=False)
    
    status: Mapped[PeriodStatus] = mapped_column(Enum(PeriodStatus, name="financial_period_status"), default=PeriodStatus.OPEN, nullable=False)
    
    opened_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True)

    __table_args__ = (
        UniqueConstraint("organisation_id", "period_name", name="uq_financial_period_org_name"),
    )
