import enum
import uuid
from sqlalchemy import Enum, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class OperatingUnitStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"

class OperatingUnit(Base, TimestampMixin):
    __tablename__ = "operating_units"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[OperatingUnitStatus] = mapped_column(
        Enum(OperatingUnitStatus, name="operating_unit_status"), 
        default=OperatingUnitStatus.ACTIVE, 
        nullable=False
    )

    # Relationships
    organisation = relationship("app.modules.identity.organisations.models.Organisation")
    locations: Mapped[list["OperatingUnitLocation"]] = relationship(
        "OperatingUnitLocation", 
        back_populates="operating_unit",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("organisation_id", "code", name="uq_org_ou_code"),
        UniqueConstraint("id", "organisation_id", name="uq_ou_id_organisation_id"),
    )

class OperatingUnitLocation(Base, TimestampMixin):
    __tablename__ = "operating_unit_locations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    operating_unit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    
    # Basic address fields
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Geolocation
    latitude: Mapped[str | None] = mapped_column(String(50), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    status: Mapped[OperatingUnitStatus] = mapped_column(
        Enum(OperatingUnitStatus, name="operating_unit_status", create_type=False),
        default=OperatingUnitStatus.ACTIVE,
        nullable=False
    )

    # Relationships
    operating_unit: Mapped["OperatingUnit"] = relationship(
        "OperatingUnit", 
        back_populates="locations"
    )

    __table_args__ = (
        UniqueConstraint("operating_unit_id", "code", name="uq_ou_location_code"),
        ForeignKeyConstraint(
            ["operating_unit_id", "organisation_id"],
            ["operating_units.id", "operating_units.organisation_id"],
            ondelete="CASCADE",
            name="fk_ou_location_ou_org"
        ),
    )
