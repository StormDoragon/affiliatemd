"""
Earnings tracking and revenue-share calculation service.
Aggregates affiliate earnings by cluster/post and calculates Elite tier payouts.
"""

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.content_item import ContentItem
from ..models.earning_event import EarningEvent


class EarningsTracker:
    """Track and aggregate affiliate earnings."""

    def __init__(self, db: Session | None = None):
        self.db = db

    def _resolve_db(self, db: Session | None = None) -> Session:
        resolved = db or self.db
        if resolved is None:
            raise ValueError("Database session is required")
        return resolved

    def get_user_earnings(self, user_id: str, days: int = 30) -> dict:
        """Get user's total earnings for past N days."""
        db = self._resolve_db()
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        total = (
            db.query(func.sum(EarningEvent.amount))
            .filter(
                EarningEvent.owner_id == int(user_id),
                EarningEvent.created_at >= cutoff_date,
            )
            .scalar()
            or 0.0
        )

        return {
            "total_earnings": float(total),
            "period_days": days,
        }

    def get_monthly_summary(self, user_id: str, month: date = None) -> dict:
        """Get earnings summary for a specific month."""
        db = self._resolve_db()
        if not month:
            month = date.today().replace(day=1)
        else:
            month = month.replace(day=1)

        month_start = datetime(month.year, month.month, 1)
        month_end = month_start + relativedelta(months=1)

        total = (
            db.query(func.sum(EarningEvent.amount))
            .filter(
                EarningEvent.owner_id == int(user_id),
                EarningEvent.created_at >= month_start,
                EarningEvent.created_at < month_end,
            )
            .scalar()
            or 0.0
        )

        order_count = (
            db.query(func.count(EarningEvent.id))
            .filter(
                EarningEvent.owner_id == int(user_id),
                EarningEvent.created_at >= month_start,
                EarningEvent.created_at < month_end,
            )
            .scalar()
            or 0
        )

        avg_order = float(total) / max(order_count, 1)

        return {
            "month": month.isoformat(),
            "total_earnings": float(total),
            "order_count": order_count,
            "avg_order_value": round(avg_order, 2),
        }

    def calculate_revenue_share(self, user_id: str, month: date = None) -> dict:
        """Calculate 12% revenue share for Elite tier."""
        db = self._resolve_db()
        if not month:
            month = date.today().replace(day=1)
        else:
            month = month.replace(day=1)

        month_start = datetime(month.year, month.month, 1)
        month_end = month_start + relativedelta(months=1)

        total_earnings = (
            db.query(func.sum(EarningEvent.amount))
            .filter(
                EarningEvent.owner_id == int(user_id),
                EarningEvent.created_at >= month_start,
                EarningEvent.created_at < month_end,
            )
            .scalar()
            or 0.0
        )

        revenue_share = float(total_earnings) * 0.12

        return {
            "period_start": month.isoformat(),
            "period_end": (month_end - timedelta(days=1)).date().isoformat(),
            "total_earnings": float(total_earnings),
            "revenue_share_amount": round(revenue_share, 2),
        }

    def owned_usd(self, db: Session, owner_id: int):
        return (
            db.query(EarningEvent)
            .join(ContentItem, ContentItem.id == EarningEvent.content_item_id)
            .filter(
                EarningEvent.owner_id == owner_id,
                ContentItem.owner_id == owner_id,
                func.upper(EarningEvent.currency) == "USD",
            )
        )

    def summarize(self, db: Session | None = None, owner_id: int = 0) -> dict:
        resolved_db = self._resolve_db(db)
        revenue, earnings_count = (
            self.owned_usd(resolved_db, owner_id)
            .with_entities(
                func.coalesce(func.sum(EarningEvent.amount), 0),
                func.count(EarningEvent.id),
            )
            .one()
        )
        posts_count = (
            resolved_db.query(ContentItem).filter(ContentItem.owner_id == owner_id).count()
        )

        return {
            "posts_count": posts_count,
            "revenue": float(revenue),
            "earnings_count": earnings_count,
            "epc": round(float(revenue) / posts_count, 2) if posts_count else 0.0,
        }
