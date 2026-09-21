import enum
import uuid
from sqlalchemy import Enum, ForeignKey, ForeignKeyConstraint, String, UniqueConstraint, DECIMAL, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class ClientStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ONBOARDING = "ONBOARDING"
    SUSPENDED = "SUSPENDED"

class Client(Base, TimestampMixin):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    contact_person: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    billing_address: Mapped[str | None] = mapped_column(String, nullable=True)
    gstin: Mapped[str | None] = mapped_column(String(15), nullable=True)
    pan: Mapped[str | None] = mapped_column(String(10), nullable=True)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30)
    credit_limit: Mapped[float] = mapped_column(DECIMAL, default=0.0)
    status: Mapped[ClientStatus] = mapped_column(Enum(ClientStatus, name="client_status"), default=ClientStatus.ACTIVE, nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)

    locations: Mapped[list["ClientLocation"]] = relationship("ClientLocation", back_populates="client", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("id", "organisation_id", name="uq_client_id_organisation_id"),
    )

class ClientLocation(Base, TimestampMixin):
    __tablename__ = "client_locations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    operating_unit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    address: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[ClientStatus] = mapped_column(Enum(ClientStatus, name="client_status", create_type=False), default=ClientStatus.ACTIVE, nullable=False)

    client: Mapped["Client"] = relationship("Client", back_populates="locations")
    operating_unit = relationship("app.modules.operations.operating_units.models.OperatingUnit")

    __table_args__ = (
        ForeignKeyConstraint(
            ["client_id", "organisation_id"],
            ["clients.id", "clients.organisation_id"],
            name="fk_client_location_client_org",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["operating_unit_id", "organisation_id"],
            ["operating_units.id", "operating_units.organisation_id"],
            name="fk_client_location_ou_org",
            ondelete="SET NULL",
        ),
        UniqueConstraint("id", "organisation_id", name="uq_client_location_id_organisation_id"),
    )

class ClientOperatingUnit(Base, TimestampMixin):
    __tablename__ = "client_operating_units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    operating_unit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)

    __table_args__ = (
        UniqueConstraint("client_id", "operating_unit_id", name="uq_client_ou"),
        ForeignKeyConstraint(
            ["client_id", "organisation_id"],
            ["clients.id", "clients.organisation_id"],
            name="fk_client_ou_client_org",
            ondelete="CASCADE",
        ),
        # Assuming operating_units has unique constraint on id and organisation_id (added just now)
        ForeignKeyConstraint(
            ["operating_unit_id", "organisation_id"],
            ["operating_units.id", "operating_units.organisation_id"],
            name="fk_client_ou_ou_org",
            ondelete="CASCADE",
        ),
    )

class ClientLocationOUHistory(Base, TimestampMixin):
    __tablename__ = "client_location_ou_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_location_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    previous_operating_unit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    new_operating_unit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    reason: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["client_location_id", "organisation_id"],
            ["client_locations.id", "client_locations.organisation_id"],
            name="fk_history_client_location_org",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["previous_operating_unit_id", "organisation_id"],
            ["operating_units.id", "operating_units.organisation_id"],
            name="fk_history_prev_ou_org",
            ondelete="SET NULL",
        ),
        ForeignKeyConstraint(
            ["new_operating_unit_id", "organisation_id"],
            ["operating_units.id", "operating_units.organisation_id"],
            name="fk_history_new_ou_org",
            ondelete="SET NULL",
        ),
    )
