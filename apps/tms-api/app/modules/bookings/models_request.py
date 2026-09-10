import datetime
import enum
import uuid
from decimal import Decimal
from sqlalchemy import DateTime, Enum, Float, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class BookingRequestStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    REQUESTED = "REQUESTED"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class BookingType(str, enum.Enum):
    ETS = "ETS"
    SPOT = "SPOT"
    FIXED = "FIXED"
    RENTAL = "RENTAL"
    AIRPORT = "AIRPORT"
    LOCAL = "LOCAL"
    OUTSTATION = "OUTSTATION"
    CORPORATE = "CORPORATE"
    CONTRACT = "CONTRACT"
    RECURRING = "RECURRING"


class BookingServiceType(str, enum.Enum):
    PASSENGER = "PASSENGER"
    CARGO = "CARGO"


class BookingRequest(Base, TimestampMixin):
    __tablename__ = "booking_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    request_number: Mapped[str] = mapped_column(String(64), nullable=False)
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    booking_type: Mapped[BookingType] = mapped_column(
        Enum(BookingType, name="booking_type"),
        default=BookingType.SPOT,
        nullable=False,
    )
    service_type: Mapped[BookingServiceType] = mapped_column(
        Enum(BookingServiceType, name="booking_service_type"),
        default=BookingServiceType.CARGO,
        nullable=False,
    )
    pickup_address: Mapped[str] = mapped_column(Text, nullable=False)
    pickup_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    pickup_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    drop_address: Mapped[str] = mapped_column(Text, nullable=False)
    drop_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    drop_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    pickup_datetime: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expected_completion_datetime: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Polymorphic Passenger & Cargo data
    passenger_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    cargo_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    vehicle_requirements: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    special_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(64), default="MANUAL", nullable=False)
    
    rate_card_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rate_card_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    estimated_pricing: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[BookingRequestStatus] = mapped_column(
        Enum(BookingRequestStatus, name="booking_request_status"),
        default=BookingRequestStatus.DRAFT,
        nullable=False,
    )
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    organisation = relationship("Organisation", lazy="selectin")
    customer = relationship("Customer", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organisation_id", "request_number", name="uq_booking_req_org_num"),
    )
