"""prince: reference images and music

Revision ID: 0004
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("refs", sa.JSON))
    op.add_column("orders", sa.Column("music", sa.String(64)))


def downgrade() -> None:
    op.drop_column("orders", "music")
    op.drop_column("orders", "refs")
