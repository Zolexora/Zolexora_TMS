import datetime
import enum
import uuid
from decimal import Decimal
from sqlalchemy import CheckConstraint, Date, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class VehicleBodyType(str, enum.Enum):
    TRUCK = "TRUCK"
    TRAILER = "TRAILER"
    CONTAINER = "CONTAINER"
    TANKER = "TANKER"
    TIPPER = "TIPPER"
    TEMPO = "TEMPO"
    PICKUP = "PICKUP"
    OTHER = "OTHER"


class VehicleOwnershipType(str, enum.Enum):
    OWNED = "OWNED"
    LEASED = "LEASED"
    ATTACHED = "ATTACHED"


class FuelType(str, enum.Enum):
    DIESEL = "DIESEL"
    CNG = "CNG"
    ELECTRIC = "ELECTRIC"
    PETROL = "PETROL"


class VehicleOperationalStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ON_DUTY = "ON_DUTY"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class Vehicle(Base, TimestampMixin):
    __tablename__ = "vehicles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    registration_number: Mapped[str] = mapped_column(String(32), nullable=False)
    vehicle_type: Mapped[VehicleBodyType] = mapped_column(
        Enum(VehicleBodyType, name="vehicle_body_type"),
        default=VehicleBodyType.TRUCK,
        nullable=False,
    )
    ownership_type: Mapped[VehicleOwnershipType] = mapped_column(
        Enum(VehicleOwnershipType, name="vehicle_ownership_type"),
        default=VehicleOwnershipType.OWNED,
        nullable=False,
    )
    make: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuel_type: Mapped[FuelType] = mapped_column(
        Enum(FuelType, name="fuel_type"),
        default=FuelType.DIESEL,
        nullable=False,
    )
    payload_capacity_kg: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    volume_cft: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    odometer_km: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.0"), nullable=False)
    fastag_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    gps_device_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rc_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rc_expiry: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    fitness_expiry: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    permit_expiry: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    insurance_expiry: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    puc_expiry: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    status: Mapped[VehicleOperationalStatus] = mapped_column(
        Enum(VehicleOperationalStatus, name="vehicle_operational_status"),
        default=VehicleOperationalStatus.AVAILABLE,
        nullable=False,
    )
    documents: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)

    organisation = relationship("Organisation", lazy="selectin")
    vendor = relationship("Vendor", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("organisation_id", "registration_number", name="uq_vehicle_org_reg"),
        CheckConstraint("length(trim(registration_number)) between 4 and 32", name="ck_vehicle_reg_len"),
    )
