"""photos on orders, cards versions

Revision ID: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("photos", sa.JSON))
    op.add_column("orders", sa.Column("ready_at", sa.DateTime(timezone=True)))
    op.create_table(
        "cards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("order_id", sa.Integer, sa.ForeignKey("orders.id"), nullable=False, index=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("kind", sa.String(16), nullable=False, server_default="generate"),
        sa.Column("spec", sa.JSON, nullable=False),
        sa.Column("usage", sa.JSON),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("cards")
    op.drop_column("orders", "ready_at")
    op.drop_column("orders", "photos")
