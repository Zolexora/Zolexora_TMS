import datetime
import enum
import uuid
from decimal import Decimal
from sqlalchemy import CheckConstraint, DateTime, Enum, Float, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class TripStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_TRANSIT = "IN_TRANSIT"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Trip(Base, TimestampMixin):
    __tablename__ = "trips"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trip_number: Mapped[str] = mapped_column(String(64), nullable=False)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    duty_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("duties.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
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
    start_odometer: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    end_odometer: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    total_distance_km: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    start_timestamp: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_timestamp: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    start_location: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    end_location: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    toll_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"), nullable=False)
    fuel_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"), nullable=False)
    parking_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.0"), nullable=False)
    waiting_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    status: Mapped[TripStatus] = mapped_column(
        Enum(TripStatus, name="trip_lifecycle_status"),
        default=TripStatus.NOT_STARTED,
        nullable=False,
        index=True,
    )
    
    pod_attachment_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pod_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pod_uploaded_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    operational_receipts: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    organisation = relationship("Organisation", lazy="selectin")
    duty = relationship("Duty", back_populates="trip")
    driver = relationship("Driver", lazy="selectin")
    vehicle = relationship("Vehicle", lazy="selectin")
    events = relationship("TripEvent", back_populates="trip", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organisation_id", "trip_number", name="uq_trip_org_num"),
        CheckConstraint("end_odometer IS NULL OR end_odometer >= start_odometer", name="ck_trip_odometer_valid"),
    )


class TripEvent(Base):
    __tablename__ = "trip_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    trip = relationship("Trip", back_populates="events")
