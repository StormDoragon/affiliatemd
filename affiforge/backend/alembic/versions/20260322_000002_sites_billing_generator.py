"""add sites billing and generator fields

Revision ID: 20260322_000002
Revises: 20260322_000001
Create Date: 2026-03-22 00:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260322_000002"
down_revision = "20260322_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("stripe_customer_id", sa.String(length=255), nullable=True))
    op.add_column(
        "users",
        sa.Column("profitshare_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )

    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("wp_url", sa.String(length=255), nullable=False),
        sa.Column("wp_username", sa.String(length=255), nullable=False),
        sa.Column("wp_app_password", sa.String(length=255), nullable=False),
        sa.Column("amazon_tag", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f("ix_sites_id"), "sites", ["id"], unique=False)
    op.create_index(op.f("ix_sites_user_id"), "sites", ["user_id"], unique=False)

    op.add_column("content_items", sa.Column("keyword", sa.String(length=255), nullable=True))
    op.add_column("content_items", sa.Column("reddit_thread_id", sa.String(length=255), nullable=True))
    op.add_column(
        "content_items",
        sa.Column("revenue_attributed", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    op.add_column(
        "content_items",
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("content_items", "site_id")
    op.drop_column("content_items", "revenue_attributed")
    op.drop_column("content_items", "reddit_thread_id")
    op.drop_column("content_items", "keyword")

    op.drop_index(op.f("ix_sites_user_id"), table_name="sites")
    op.drop_index(op.f("ix_sites_id"), table_name="sites")
    op.drop_table("sites")

    op.drop_column("users", "profitshare_enabled")
    op.drop_column("users", "stripe_customer_id")
