import enum
import uuid
from sqlalchemy import Enum, ForeignKey, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin

class VendorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ONBOARDING = "ONBOARDING"
    SUSPENDED = "SUSPENDED"

class VendorType(str, enum.Enum):
    TRANSPORTER = "TRANSPORTER"
    BROKER = "BROKER"
    FUEL_STATION = "FUEL_STATION"
    MAINTENANCE = "MAINTENANCE"
    OTHER = "OTHER"

class Vendor(Base, TimestampMixin):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    vendor_type: Mapped[VendorType] = mapped_column(Enum(VendorType, name="vendor_type", create_type=False), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[VendorStatus] = mapped_column(Enum(VendorStatus, name="vendor_status", create_type=False), default=VendorStatus.ACTIVE, nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
