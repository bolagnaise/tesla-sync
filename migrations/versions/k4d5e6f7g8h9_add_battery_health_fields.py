"""Add battery health fields for mobile app sync

Revision ID: k4d5e6f7g8h9
Revises: j3c4d5e6f7g8
Create Date: 2025-12-17 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k4d5e6f7g8h9'
down_revision = 'j3c4d5e6f7g8'
branch_labels = None
depends_on = None


def upgrade():
    # Add battery health fields to user table
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('battery_original_capacity_wh', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('battery_current_capacity_wh', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('battery_degradation_percent', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('battery_count', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('battery_health_updated', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('battery_health_api_token', sa.String(length=64), nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('battery_health_api_token')
        batch_op.drop_column('battery_health_updated')
        batch_op.drop_column('battery_count')
        batch_op.drop_column('battery_degradation_percent')
        batch_op.drop_column('battery_current_capacity_wh')
        batch_op.drop_column('battery_original_capacity_wh')
