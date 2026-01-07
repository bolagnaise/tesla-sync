"""Add manual_export_override fields

Revision ID: a0t1u2v3w4x5
Revises: z9s0t1u2v3w4
Create Date: 2026-01-07 22:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a0t1u2v3w4x5'
down_revision = 'z9s0t1u2v3w4'
branch_labels = None
depends_on = None


def upgrade():
    # Add manual_export_override column
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('manual_export_override', sa.Boolean(), nullable=True, default=False))
        batch_op.add_column(sa.Column('manual_export_rule', sa.String(20), nullable=True))

    # Set default values for existing rows
    op.execute("UPDATE user SET manual_export_override = 0 WHERE manual_export_override IS NULL")


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('manual_export_rule')
        batch_op.drop_column('manual_export_override')
