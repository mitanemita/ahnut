"""edits, publication, hosting terms, payment kinds

Revision ID: 0005
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

COLS = [
    sa.Column("edits_bought", sa.Integer, nullable=False, server_default="0"),
    sa.Column("edits_used", sa.Integer, nullable=False, server_default="0"),
    sa.Column("edit_error", sa.String(300)),
    sa.Column("card_id", sa.String(32), unique=True),
    sa.Column("card_password", sa.String(200)),
    sa.Column("published_at", sa.DateTime(timezone=True)),
    sa.Column("expires_at", sa.DateTime(timezone=True)),
    sa.Column("forever", sa.Boolean, nullable=False, server_default=sa.false()),
    sa.Column("reminder_sent_at", sa.DateTime(timezone=True)),
    sa.Column("purged_at", sa.DateTime(timezone=True)),
]


def upgrade() -> None:
    for c in COLS:
        op.add_column("orders", c)
    op.add_column("payments", sa.Column("meta", sa.JSON))
    op.add_column("payments", sa.Column("applied", sa.Boolean, nullable=False, server_default=sa.false()))
    op.execute("UPDATE payments SET applied = true WHERE status = 'succeeded'")


def downgrade() -> None:
    op.drop_column("payments", "applied")
    op.drop_column("payments", "meta")
    for c in reversed(COLS):
        op.drop_column("orders", c.name)
