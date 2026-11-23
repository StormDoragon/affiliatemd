"""Store publishing receipts and isolate draft slugs by owner."""

import sqlalchemy as sa
from alembic import op

revision = "20261123_000003"
down_revision = "20260322_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("content_items", sa.Column("publish_key", sa.String(64)))
    op.add_column("content_items", sa.Column("published_url", sa.String(2048)))
    op.drop_index("ix_content_items_slug", table_name="content_items")
    op.create_index("ix_content_owner_slug", "content_items", ["owner_id", "slug"], unique=True)
    op.create_index("ix_earnings_owner_post", "earning_events", ["owner_id", "content_item_id"])
    with op.batch_alter_table("earning_events") as batch:
        batch.alter_column(
            "amount",
            existing_type=sa.Float(),
            type_=sa.Numeric(12, 2),
            postgresql_using="round(amount::numeric, 2)",
        )
        batch.add_column(sa.Column("entry_key", sa.String(36)))
    op.create_index(
        "ix_earnings_owner_entry", "earning_events", ["owner_id", "entry_key"], unique=True
    )
    # Ciphertext can exceed the old 255-character password limit.
    with op.batch_alter_table("sites") as batch:
        batch.alter_column("wp_app_password", existing_type=sa.String(255), type_=sa.Text())


def downgrade() -> None:
    raise RuntimeError("Restore a pre-upgrade backup to roll back this migration")
