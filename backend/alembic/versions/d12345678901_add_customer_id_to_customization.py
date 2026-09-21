"""add customer_id to customization

Revision ID: d12345678901
Revises: 5cf10f6c9db7
Create Date: 2026-09-15 08:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd12345678901'
down_revision: Union[str, Sequence[str], None] = '5cf10f6c9db7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    tables = [
        'application_modules',
        'application_configurations',
        'application_workflows',
        'application_rules',
        'application_forms',
        'application_reports',
        'application_approvals'
    ]
    for table in tables:
        op.add_column(table, sa.Column('customer_id', sa.UUID(), nullable=True))
        op.create_index(op.f(f'ix_{table}_customer_id'), table, ['customer_id'], unique=False)

def downgrade() -> None:
    tables = [
        'application_modules',
        'application_configurations',
        'application_workflows',
        'application_rules',
        'application_forms',
        'application_reports',
        'application_approvals'
    ]
    for table in tables:
        op.drop_index(op.f(f'ix_{table}_customer_id'), table_name=table)
        op.drop_column(table, 'customer_id')
