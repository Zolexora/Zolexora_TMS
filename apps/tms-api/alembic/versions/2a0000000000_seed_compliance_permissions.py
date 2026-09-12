"""seed_compliance_permissions

Revision ID: 2a0000000000
Revises: 1f4636f4238e
Create Date: 2026-09-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision: str = '2a0000000000'
down_revision: Union[str, None] = '1f4636f4238e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    now = datetime.now(timezone.utc)
    
    roles_table = sa.table(
        'roles',
        sa.column('id', sa.UUID),
        sa.column('code', sa.String),
    )
    permissions_table = sa.table(
        'permissions',
        sa.column('id', sa.UUID),
        sa.column('code', sa.String),
        sa.column('description', sa.String),
        sa.column('created_at', sa.DateTime(timezone=True)),
    )
    role_perms_table = sa.table(
        'role_permissions',
        sa.column('role_id', sa.UUID),
        sa.column('permission_id', sa.UUID),
    )

    perms_data = [
        ('compliance.view', 'View operational compliance requirements and records'),
        ('compliance.create', 'Upload or declare compliance documents and records'),
        ('compliance.update', 'Update compliance document metadata'),
        ('compliance.verify', 'Formally verify and accept compliance records'),
        ('compliance.override', 'Override or waive compliance blocking requirements'),
        ('compliance.manage_rules', 'Create and manage custom organisational compliance rules'),
    ]
    
    inserted_perms = []
    for code, desc in perms_data:
        p_id = uuid.uuid4()
        inserted_perms.append({'id': p_id, 'code': code, 'description': desc, 'created_at': now})

    op.bulk_insert(permissions_table, inserted_perms)

    # Get COMMANDER role id
    conn = op.get_bind()
    commander_res = conn.execute(sa.text("SELECT id FROM roles WHERE code = 'COMMANDER'"))
    commander_id = commander_res.scalar()
    
    admin_res = conn.execute(sa.text("SELECT id FROM roles WHERE code = 'ADMIN'"))
    admin_id = admin_res.scalar()
    
    dispatcher_res = conn.execute(sa.text("SELECT id FROM roles WHERE code = 'DISPATCHER'"))
    dispatcher_id = dispatcher_res.scalar()
    
    if commander_id:
        op.bulk_insert(role_perms_table, [{'role_id': commander_id, 'permission_id': p['id']} for p in inserted_perms])
        
    if admin_id:
        op.bulk_insert(role_perms_table, [{'role_id': admin_id, 'permission_id': p['id']} for p in inserted_perms])
        
    if dispatcher_id:
        view_perm = next(p['id'] for p in inserted_perms if p['code'] == 'compliance.view')
        op.bulk_insert(role_perms_table, [{'role_id': dispatcher_id, 'permission_id': view_perm}])


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM permissions WHERE code IN ('compliance.view', 'compliance.create', 'compliance.update', 'compliance.verify', 'compliance.override', 'compliance.manage_rules')")
    )
