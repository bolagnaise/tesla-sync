"""Add network tariff configuration for Flow Power AEMO

Revision ID: g9b4d8f03e25
Revises: f8a3c7e92d14
Create Date: 2025-12-13 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g9b4d8f03e25'
down_revision = 'f8a3c7e92d14'
branch_labels = None
depends_on = None


def upgrade():
    # Add network tariff configuration columns
    # These are used for Flow Power + AEMO to add DNSP (network) charges
    # to the wholesale prices since AEMO doesn't include them
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('network_tariff_type', sa.String(10), nullable=True, default='flat'))
        batch_op.add_column(sa.Column('network_flat_rate', sa.Float(), nullable=True, default=8.0))
        batch_op.add_column(sa.Column('network_peak_rate', sa.Float(), nullable=True, default=15.0))
        batch_op.add_column(sa.Column('network_shoulder_rate', sa.Float(), nullable=True, default=5.0))
        batch_op.add_column(sa.Column('network_offpeak_rate', sa.Float(), nullable=True, default=2.0))
        batch_op.add_column(sa.Column('network_peak_start', sa.String(5), nullable=True, default='16:00'))
        batch_op.add_column(sa.Column('network_peak_end', sa.String(5), nullable=True, default='21:00'))
        batch_op.add_column(sa.Column('network_offpeak_start', sa.String(5), nullable=True, default='10:00'))
        batch_op.add_column(sa.Column('network_offpeak_end', sa.String(5), nullable=True, default='15:00'))
        batch_op.add_column(sa.Column('network_other_fees', sa.Float(), nullable=True, default=1.5))
        batch_op.add_column(sa.Column('network_include_gst', sa.Boolean(), nullable=True, default=True))


def downgrade():
    # Remove network tariff configuration columns
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('network_include_gst')
        batch_op.drop_column('network_other_fees')
        batch_op.drop_column('network_offpeak_end')
        batch_op.drop_column('network_offpeak_start')
        batch_op.drop_column('network_peak_end')
        batch_op.drop_column('network_peak_start')
        batch_op.drop_column('network_offpeak_rate')
        batch_op.drop_column('network_shoulder_rate')
        batch_op.drop_column('network_peak_rate')
        batch_op.drop_column('network_flat_rate')
        batch_op.drop_column('network_tariff_type')
