filepath = "apps/backend/app/modules/identity/organisations/membership_models.py"

with open(filepath, "r") as f:
    content = f.read()

# Add is_commander
content = content.replace("is_creator: Mapped[bool] = mapped_column(default=False, nullable=False)", "is_creator: Mapped[bool] = mapped_column(default=False, nullable=False)\n    is_commander: Mapped[bool] = mapped_column(default=False, nullable=False)")

# Add index
content = content.replace("UniqueConstraint(\"organisation_id\", \"user_id\", name=\"uq_org_member_org_user\"),", "UniqueConstraint(\"organisation_id\", \"user_id\", name=\"uq_org_member_org_user\"),\n        Index(\"uq_org_member_commander\", \"organisation_id\", unique=True, postgresql_where=text(\"is_commander = true\")),\n")

# Need to import text if not there
content = content.replace("from sqlalchemy import Enum, ForeignKey, UniqueConstraint, DateTime", "from sqlalchemy import Enum, ForeignKey, UniqueConstraint, DateTime, Index, text")

with open(filepath, "w") as f:
    f.write(content)
