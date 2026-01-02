"""Add inverter_restore_soc column for configurable restore threshold

Revision ID: z9s0t1u2v3w4
Revises: y8r9s0t1u2v3
Create Date: 2026-01-02 13:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'z9s0t1u2v3w4'
down_revision = 'y8r9s0t1u2v3'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('inverter_restore_soc', sa.Integer(), nullable=True, default=98))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('inverter_restore_soc')
