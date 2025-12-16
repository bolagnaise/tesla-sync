"""Add export boost fields for Amber users

Revision ID: i2b3c4d5e6f7
Revises: 546b2ceef0e5
Create Date: 2025-12-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i2b3c4d5e6f7'
down_revision = '546b2ceef0e5'
branch_labels = None
depends_on = None


def upgrade():
    # Add export boost configuration fields
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('export_boost_enabled', sa.Boolean(), server_default='0'))
        batch_op.add_column(sa.Column('export_price_offset', sa.Float(), server_default='0.0'))
        batch_op.add_column(sa.Column('export_min_price', sa.Float(), server_default='0.0'))
        batch_op.add_column(sa.Column('export_boost_start', sa.String(5), server_default='17:00'))
        batch_op.add_column(sa.Column('export_boost_end', sa.String(5), server_default='21:00'))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('export_boost_end')
        batch_op.drop_column('export_boost_start')
        batch_op.drop_column('export_min_price')
        batch_op.drop_column('export_price_offset')
        batch_op.drop_column('export_boost_enabled')
