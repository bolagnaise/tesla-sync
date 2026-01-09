"""Add fronius_load_following column

Revision ID: b1u2v3w4x5y6
Revises: a0t1u2v3w4x5
Create Date: 2026-01-09 20:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1u2v3w4x5y6'
down_revision = 'a0t1u2v3w4x5'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fronius_load_following', sa.Boolean(), nullable=True, default=False))

    # Set default value for existing rows
    op.execute("UPDATE user SET fronius_load_following = 0 WHERE fronius_load_following IS NULL")


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('fronius_load_following')
