"""add_dco_and_emi_enums

Revision ID: ad3946b45aba
Revises: 2a0000000000
Create Date: 2026-09-12 07:05:29.362761

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad3946b45aba'
down_revision: Union[str, Sequence[str], None] = '2a0000000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new values to vendor_type enum
    op.execute("ALTER TYPE vendor_type ADD VALUE IF NOT EXISTS 'DCO'")
    op.execute("ALTER TYPE vendor_type ADD VALUE IF NOT EXISTS 'EMI_DRIVER'")
    
    # Add new values to vehicle_ownership_type enum
    op.execute("ALTER TYPE vehicle_ownership_type ADD VALUE IF NOT EXISTS 'EMI'")


def downgrade() -> None:
    # PostgreSQL does not support removing values from an ENUM type easily.
    pass
