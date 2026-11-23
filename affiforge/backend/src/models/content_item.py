from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class ContentItem(Base):
    __tablename__ = "content_items"
    __table_args__ = (Index("ix_content_owner_slug", "owner_id", "slug", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    keyword: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reddit_thread_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publish_key: Mapped[str | None] = mapped_column(String(64))
    published_url: Mapped[str | None] = mapped_column(String(2048))
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    revenue_attributed: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), nullable=False
    )
    site_id: Mapped[int | None] = mapped_column(
        ForeignKey("sites.id", ondelete="SET NULL"), nullable=True
    )
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
