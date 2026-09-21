import enum
import uuid
import datetime
from sqlalchemy import Enum, ForeignKey, UniqueConstraint, DateTime, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class MemberStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    SUSPENDED = "SUSPENDED"


class OrganisationMember(Base, TimestampMixin):
    __tablename__ = "organisation_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    organisation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    status: Mapped[MemberStatus] = mapped_column(
        Enum(MemberStatus, name="member_status"), default=MemberStatus.ACTIVE, nullable=False
    )
    is_creator: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_commander: Mapped[bool] = mapped_column(default=False, nullable=False)

    organisation: Mapped["Organisation"] = relationship("Organisation")

    __table_args__ = (
        UniqueConstraint("organisation_id", "user_id", name="uq_org_member_org_user"),
        Index("uq_org_member_commander", "organisation_id", unique=True, postgresql_where=text("is_commander = true")),

    )

class OrganisationInvitation(Base, TimestampMixin):
    __tablename__ = "organisation_invitations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organisation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(nullable=False, index=True)
    token: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(default="PENDING", nullable=False) # PENDING, ACCEPTED, REVOKED, EXPIRED
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
