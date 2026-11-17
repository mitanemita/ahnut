"""orders: choice, payment, answers; payments table

Revision ID: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for col in (
        sa.Column("recipient", sa.String(24)),
        sa.Column("occasion", sa.String(32)),
        sa.Column("tone", sa.String(24)),
        sa.Column("email", sa.String(254)),
        sa.Column("amount_rub", sa.Integer, nullable=False, server_default="0"),
        sa.Column("paid", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("answers", sa.JSON),
        sa.Column("answers_complete", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("pd_consent_at", sa.DateTime(timezone=True)),
        sa.Column("generation_requested_at", sa.DateTime(timezone=True)),
    ):
        op.add_column("orders", col)
    op.create_table(
        "payments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("order_id", sa.Integer, sa.ForeignKey("orders.id"), nullable=False, index=True),
        sa.Column("yookassa_id", sa.String(64), nullable=False, unique=True),
        sa.Column("kind", sa.String(16), nullable=False, server_default="order"),
        sa.Column("amount_rub", sa.Integer, nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("payments")
    for c in ("generation_requested_at", "pd_consent_at", "answers_complete", "answers", "paid_at", "paid",
              "amount_rub", "email", "tone", "occasion", "recipient"):
        op.drop_column("orders", c)
