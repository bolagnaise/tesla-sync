"""Add spike_protection_enabled field for anti-arbitrage during Amber spikes

Revision ID: m6f7g8h9i0j1
Revises: l5e6f7g8h9i0
Create Date: 2024-12-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'm6f7g8h9i0j1'
down_revision = 'l5e6f7g8h9i0'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    bind = op.get_bind()
    result = bind.execute(sa.text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result]
    return column_name in columns


def upgrade():
    # Add spike_protection_enabled field (default True - enabled for all users)
    if not column_exists('user', 'spike_protection_enabled'):
        op.add_column('user', sa.Column('spike_protection_enabled', sa.Boolean(), nullable=True, server_default='1'))

    # Set default value for existing users (protection enabled by default)
    op.execute("UPDATE user SET spike_protection_enabled = 1 WHERE spike_protection_enabled IS NULL")


def downgrade():
    if column_exists('user', 'spike_protection_enabled'):
        op.drop_column('user', 'spike_protection_enabled')
