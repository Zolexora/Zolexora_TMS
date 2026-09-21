import enum
import uuid
from sqlalchemy import CheckConstraint, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class OrganisationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    ARCHIVED = "ARCHIVED"


class OrganisationType(str, enum.Enum):
    SOLE_PROPRIETORSHIP = "Sole Proprietorship / Proprietor"
    PARTNERSHIP = "Partnership Firm"
    LLP = "Limited Liability Partnership (LLP)"
    PVT_LTD = "Private Limited Company"
    PUB_LTD = "Public Limited Company"
    OPC = "One Person Company (OPC)"
    LIMITED = "Limited Company"
    SECTION_8 = "Section 8 Company"
    NON_PROFIT = "Non-Profit Organisation"
    TRUST = "Trust"
    PUBLIC_TRUST = "Public Trust"
    PRIVATE_TRUST = "Private Trust"
    CHARITABLE_TRUST = "Charitable Trust"
    SOCIETY = "Society"
    COOPERATIVE = "Co-operative Society"
    HUF = "Hindu Undivided Family (HUF)"
    GOVERNMENT = "Government Organisation"
    GOVT_DEPARTMENT = "Government Department"
    PSU = "Public Sector Undertaking (PSU)"
    MUNICIPAL = "Municipal Corporation"
    LOCAL_BODY = "Local Government Body"
    EDUCATIONAL = "Educational Institution"
    UNIVERSITY = "University"
    SCHOOL = "School"
    COLLEGE = "College"
    HOSPITAL = "Hospital"
    HEALTHCARE = "Healthcare Organisation"
    NGO = "NGO"
    RELIGIOUS = "Religious Organisation"
    FOUNDATION = "Foundation"
    FAMILY_OFFICE = "Family Office"
    STARTUP = "Startup"
    INDIVIDUAL = "Freelancer / Individual"
    SELF_EMPLOYED = "Self Employed"
    OTHER = "Other"


class Organisation(Base, TimestampMixin):
    __tablename__ = "organisations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    organisation_type: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[OrganisationStatus] = mapped_column(
        Enum(OrganisationStatus, name="organisation_status"),
        default=OrganisationStatus.ACTIVE,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("length(trim(name)) between 2 and 160", name="org_name_len_check"),
        CheckConstraint("length(trim(organisation_type)) between 2 and 120", name="org_type_len_check"),
    )
