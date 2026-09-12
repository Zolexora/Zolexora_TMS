import enum
import uuid
from sqlalchemy import CheckConstraint, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class VendorType(str, enum.Enum):
    FLEET_SUPPLIER = "FLEET_SUPPLIER"
    DCO = "DCO"  # Driver Cum Owner
    EMI_DRIVER = "EMI_DRIVER"
    WORKSHOP = "WORKSHOP"
    FUEL_PARTNER = "FUEL_PARTNER"
    BROKER = "BROKER"
    OTHER = "OTHER"


class VendorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Vendor(Base, TimestampMixin):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    vendor_type: Mapped[VendorType] = mapped_column(
        Enum(VendorType, name="vendor_type"),
        default=VendorType.FLEET_SUPPLIER,
        nullable=False,
    )
    contact_person: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(10), nullable=True)
    bank_account_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bank_ifsc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[VendorStatus] = mapped_column(
        Enum(VendorStatus, name="vendor_status"),
        default=VendorStatus.ACTIVE,
        nullable=False,
    )

    organisation = relationship("Organisation", lazy="selectin")

    __table_args__ = (
        CheckConstraint("length(trim(name)) between 2 and 160", name="ck_vendor_name_len"),
    )
