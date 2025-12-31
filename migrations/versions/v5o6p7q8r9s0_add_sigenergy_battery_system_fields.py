"""Add Sigenergy battery system fields

Revision ID: v5o6p7q8r9s0
Revises: u4n5o6p7q8r9
Create Date: 2025-12-31

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'v5o6p7q8r9s0'
down_revision = 'u4n5o6p7q8r9'
branch_labels = None
depends_on = None


def upgrade():
    # Add battery system selection and Sigenergy credential columns
    with op.batch_alter_table('user', schema=None) as batch_op:
        # Battery system selection (tesla or sigenergy)
        batch_op.add_column(sa.Column('battery_system', sa.String(20), nullable=True, server_default='tesla'))

        # Sigenergy cloud API credentials
        batch_op.add_column(sa.Column('sigenergy_username', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('sigenergy_pass_enc_encrypted', sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column('sigenergy_device_id', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('sigenergy_station_id', sa.String(50), nullable=True))

        # Sigenergy OAuth tokens
        batch_op.add_column(sa.Column('sigenergy_access_token_encrypted', sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column('sigenergy_refresh_token_encrypted', sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column('sigenergy_token_expires_at', sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('sigenergy_token_expires_at')
        batch_op.drop_column('sigenergy_refresh_token_encrypted')
        batch_op.drop_column('sigenergy_access_token_encrypted')
        batch_op.drop_column('sigenergy_station_id')
        batch_op.drop_column('sigenergy_device_id')
        batch_op.drop_column('sigenergy_pass_enc_encrypted')
        batch_op.drop_column('sigenergy_username')
        batch_op.drop_column('battery_system')
