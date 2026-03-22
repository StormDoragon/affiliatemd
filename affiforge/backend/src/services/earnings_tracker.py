"""
Earnings tracking and revenue-share calculation service.
Aggregates affiliate earnings by cluster/post and calculates Elite tier payouts.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from ..models.earning_event import EarningEvent
from ..models.content_item import ContentItem


class EarningsTracker:
    """Track and aggregate affiliate earnings."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_earnings(self, user_id: str, days: int = 30) -> dict:
        """Get user's total earnings for past N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        total = self.db.query(func.sum(EarningEvent.earning_amount)).filter(
            EarningEvent.user_id == user_id,
            EarningEvent.order_date >= cutoff_date,
        ).scalar() or 0.0
        
        return {
            "total_earnings": float(total),
            "period_days": days,
        }
    
    def get_monthly_summary(self, user_id: str, month: date = None) -> dict:
        """Get earnings summary for a specific month."""
        if not month:
            month = date.today().replace(day=1)
        else:
            month = month.replace(day=1)
        
        month_end = (month + relativedelta(months=1)) - timedelta(days=1)
        
        total = self.db.query(func.sum(EarningEvent.earning_amount)).filter(
            EarningEvent.user_id == user_id,
            EarningEvent.order_date >= month,
            EarningEvent.order_date <= month_end,
        ).scalar() or 0.0
        
        order_count = self.db.query(func.count(EarningEvent.id)).filter(
            EarningEvent.user_id == user_id,
            EarningEvent.order_date >= month,
            EarningEvent.order_date <= month_end,
        ).scalar() or 0
        
        avg_order = float(total) / max(order_count, 1)
        
        return {
            "month": month.isoformat(),
            "total_earnings": float(total),
            "order_count": order_count,
            "avg_order_value": round(avg_order, 2),
        }
    
    def calculate_revenue_share(self, user_id: str, month: date = None) -> dict:
        """Calculate 12% revenue share for Elite tier."""
        if not month:
            month = date.today().replace(day=1)
        else:
            month = month.replace(day=1)
        
        month_end = (month + relativedelta(months=1)) - timedelta(days=1)
        
        total_earnings = self.db.query(func.sum(EarningEvent.earning_amount)).filter(
            EarningEvent.user_id == user_id,
            EarningEvent.order_date >= month,
            EarningEvent.order_date <= month_end,
        ).scalar() or 0.0
        
        revenue_share = float(total_earnings) * 0.12
        
        return {
            "period_start": month.isoformat(),
            "period_end": month_end.isoformat(),
            "total_earnings": float(total_earnings),
            "revenue_share_amount": round(revenue_share, 2),
        }
    
    def summarize(self, db: Session, owner_id: int) -> dict:
        """Legacy method for backward compatibility."""
        earnings = db.query(EarningEvent).filter(EarningEvent.owner_id == owner_id).all()
        posts_count = db.query(ContentItem).filter(ContentItem.owner_id == owner_id).count()

        revenue = float(sum(item.amount for item in earnings))
        earnings_count = len(earnings)
        epc = revenue / posts_count if posts_count > 0 else 0.0

        return {
            "posts_count": posts_count,
            "revenue": round(revenue, 2),
            "earnings_count": earnings_count,
            "epc": round(epc, 2),
        }
