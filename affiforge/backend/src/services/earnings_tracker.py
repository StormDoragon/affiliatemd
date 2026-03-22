from sqlalchemy.orm import Session

from ..models.content_item import ContentItem
from ..models.earning_event import EarningEvent


class EarningsTracker:
	def summarize(self, db: Session, owner_id: int) -> dict[str, float | int]:
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
