from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models.earning_event import EarningEvent
from ..models.user import User
from ..schemas.earnings import (
    DashboardOverview,
    EarningCreate,
    EarningRead,
    EarningsSummary,
    OptimizationSuggestions,
    ProfitShareBreakdown,
)
from ..services.earnings_tracker import EarningsTracker
from ..services.optimization_service import OptimizationService
from ..services.profitshare_engine import ProfitShareEngine

router = APIRouter(prefix="/earnings", tags=["earnings"])


@router.post("/", response_model=EarningRead, status_code=status.HTTP_201_CREATED)
def create_earning(
    payload: EarningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EarningEvent:
    entry = EarningEvent(
        network=payload.network,
        amount=payload.amount,
        currency=payload.currency,
        content_item_id=payload.content_item_id,
        owner_id=current_user.id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[EarningRead])
def list_earnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EarningEvent]:
    return db.query(EarningEvent).filter(EarningEvent.owner_id == current_user.id).all()


@router.get("/summary", response_model=EarningsSummary)
def earnings_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EarningsSummary:
    tracker = EarningsTracker()
    return EarningsSummary(**tracker.summarize(db=db, owner_id=current_user.id))


@router.get("/profitshare", response_model=ProfitShareBreakdown)
def profitshare_breakdown(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfitShareBreakdown:
    tracker = EarningsTracker()
    summary = tracker.summarize(db=db, owner_id=current_user.id)
    engine = ProfitShareEngine()
    breakdown = engine.calculate(
        revenue=float(summary["revenue"]),
        enabled=current_user.profitshare_enabled,
    )
    return ProfitShareBreakdown(**breakdown)


@router.get("/suggestions", response_model=OptimizationSuggestions)
def optimization_suggestions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> OptimizationSuggestions:
    tracker = EarningsTracker()
    summary = tracker.summarize(db=db, owner_id=current_user.id)
    optimizer = OptimizationService()
    suggestions = optimizer.suggest(
        posts_count=int(summary["posts_count"]),
        total_revenue=float(summary["revenue"]),
        epc=float(summary["epc"]),
    )
    return OptimizationSuggestions(suggestions=suggestions)


@router.get("/dashboard", response_model=DashboardOverview)
def dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardOverview:
    tracker = EarningsTracker()
    summary_data = tracker.summarize(db=db, owner_id=current_user.id)

    optimizer = OptimizationService()
    suggestions = optimizer.suggest(
        posts_count=int(summary_data["posts_count"]),
        total_revenue=float(summary_data["revenue"]),
        epc=float(summary_data["epc"]),
    )

    engine = ProfitShareEngine()
    breakdown = engine.calculate(
        revenue=float(summary_data["revenue"]),
        enabled=current_user.profitshare_enabled,
    )

    return DashboardOverview(
        summary=EarningsSummary(**summary_data),
        profit_share=ProfitShareBreakdown(**breakdown),
        suggestions=suggestions,
    )
