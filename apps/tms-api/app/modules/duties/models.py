import datetime
import enum
import uuid
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class DutyStatus(str, enum.Enum):
    ALLOCATED = "ALLOCATED"
    DISPATCHED = "DISPATCHED"
    ARRIVED_PICKUP = "ARRIVED_PICKUP"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED_DROP = "ARRIVED_DROP"
    DUTY_COMPLETED = "DUTY_COMPLETED"
    CANCELLED = "CANCELLED"


class DutyAssignmentStatus(str, enum.Enum):
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


class Duty(Base, TimestampMixin):
    __tablename__ = "duties"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    duty_number: Mapped[str] = mapped_column(String(64), nullable=False)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    scheduled_start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end_time: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[DutyStatus] = mapped_column(
        Enum(DutyStatus, name="duty_lifecycle_status"),
        default=DutyStatus.ALLOCATED,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispatched_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispatched_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    organisation = relationship("Organisation", lazy="selectin")
    booking = relationship("Booking", back_populates="duties", lazy="selectin")
    driver = relationship("Driver", lazy="selectin")
    vehicle = relationship("Vehicle", lazy="selectin")
    assignments = relationship("DutyAssignment", back_populates="duty", cascade="all, delete-orphan", lazy="selectin")
    trip = relationship("Trip", back_populates="duty", uselist=False, lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organisation_id", "duty_number", name="uq_duty_org_num"),
        CheckConstraint("scheduled_end_time >= scheduled_start_time", name="ck_duty_time_range"),
    )


class DutyAssignment(Base):
    __tablename__ = "duty_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    duty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("duties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("drivers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vehicles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[DutyAssignmentStatus] = mapped_column(
        Enum(DutyAssignmentStatus, name="duty_assignment_status"),
        default=DutyAssignmentStatus.ASSIGNED,
        nullable=False,
    )
    assigned_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    accepted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    duty = relationship("Duty", back_populates="assignments")
    driver = relationship("Driver", lazy="selectin")
    vehicle = relationship("Vehicle", lazy="selectin")
