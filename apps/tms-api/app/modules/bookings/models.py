import datetime
import enum
import uuid
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin
from app.modules.bookings.models_request import BookingServiceType, BookingType


class BookingStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    booking_number: Mapped[str] = mapped_column(String(64), nullable=False)
    booking_request_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("booking_requests.id", ondelete="SET NULL"),
        nullable=True,
    )
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
        Enum(BookingType, name="booking_type", create_type=False),
        nullable=False,
    )
    service_type: Mapped[BookingServiceType] = mapped_column(
        Enum(BookingServiceType, name="booking_service_type", create_type=False),
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
    
    passenger_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    cargo_info: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    vehicle_requirements: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    driver_requirements: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    rate_card_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rate_card_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    commercial_terms: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    operational_instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_operational_status"),
        default=BookingStatus.CONFIRMED,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(String(64), default="MANUAL", nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict, nullable=False)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    organisation = relationship("Organisation", lazy="selectin")
    customer = relationship("Customer", lazy="selectin")
    duties = relationship("Duty", back_populates="booking", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organisation_id", "booking_number", name="uq_booking_org_num"),
    )
