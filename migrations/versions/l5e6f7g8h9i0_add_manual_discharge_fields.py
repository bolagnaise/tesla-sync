"""Add manual discharge mode fields

Revision ID: l5e6f7g8h9i0
Revises: k4d5e6f7g8h9
Create Date: 2024-12-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'l5e6f7g8h9i0'
down_revision = 'k4d5e6f7g8h9'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    bind = op.get_bind()
    result = bind.execute(sa.text(f"PRAGMA table_info({table_name})"))
    columns = [row[1] for row in result]
    return column_name in columns


def upgrade():
    # Add manual discharge mode fields (check if they exist first)
    if not column_exists('user', 'manual_discharge_active'):
        op.add_column('user', sa.Column('manual_discharge_active', sa.Boolean(), nullable=True, server_default='0'))

    if not column_exists('user', 'manual_discharge_expires_at'):
        op.add_column('user', sa.Column('manual_discharge_expires_at', sa.DateTime(), nullable=True))

    if not column_exists('user', 'manual_discharge_saved_tariff_id'):
        op.add_column('user', sa.Column('manual_discharge_saved_tariff_id', sa.Integer(), nullable=True))

    # Note: SQLite doesn't support adding foreign key constraints to existing tables
    # The constraint is defined in the model but won't be enforced at the DB level for SQLite


def downgrade():
    # Remove columns (check if they exist first)
    if column_exists('user', 'manual_discharge_saved_tariff_id'):
        op.drop_column('user', 'manual_discharge_saved_tariff_id')

    if column_exists('user', 'manual_discharge_expires_at'):
        op.drop_column('user', 'manual_discharge_expires_at')

    if column_exists('user', 'manual_discharge_active'):
        op.drop_column('user', 'manual_discharge_active')
