from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models.content_item import ContentItem
from ..models.earning_event import EarningEvent
from ..models.user import User
from ..schemas.earnings import (
    AdOptimizerRequest,
    AdOptimizerResponse,
    DashboardOverview,
    EarningCreate,
    EarningRead,
    EarningsSummary,
    MultiProgramDashboard,
    OptimizationSuggestions,
    PostEarnings,
    ProfitShareBreakdown,
    ProgramEarningsBreakdown,
)
from ..services.ad_revenue_optimizer import AdRevenueOptimizer
from ..services.earnings_tracker import EarningsTracker
from ..services.optimization_service import OptimizationService
from ..services.profitshare_engine import ProfitShareEngine
from .content import owned_content

router = APIRouter(prefix="/earnings", tags=["earnings"])


@router.post("/", response_model=EarningRead, status_code=status.HTTP_201_CREATED)
def create_earning(
    payload: EarningCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EarningEvent:
    owner_id = current_user.id
    owned_content(db, owner_id, payload.content_item_id)
    network = payload.network.strip().lower()
    if not network:
        raise HTTPException(422, "Enter an affiliate network")
    entry_key = str(payload.entry_key) if payload.entry_key else None
    entry = EarningEvent(
        network=network,
        amount=payload.amount,
        currency=payload.currency,
        content_item_id=payload.content_item_id,
        owner_id=owner_id,
        entry_key=entry_key,
    )
    db.add(entry)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if entry_key:
            existing = (
                db.query(EarningEvent).filter_by(owner_id=owner_id, entry_key=entry_key).first()
            )
            if existing and (
                existing.network,
                existing.amount,
                existing.content_item_id,
                existing.currency,
            ) == (network, payload.amount, payload.content_item_id, payload.currency):
                return existing
        raise HTTPException(409, "This earnings entry conflicts with an existing record") from exc
    db.refresh(entry)
    return entry


@router.get("/", response_model=list[EarningRead])
def list_earnings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EarningEvent]:
    return (
        EarningsTracker()
        .owned_usd(db, current_user.id)
        .order_by(EarningEvent.id.desc())
        .limit(100)
        .all()
    )


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

    earning_totals = (
        tracker.owned_usd(db, current_user.id)
        .with_entities(EarningEvent.content_item_id, func.sum(EarningEvent.amount).label("revenue"))
        .group_by(EarningEvent.content_item_id)
        .subquery()
    )
    posts = (
        db.query(ContentItem, earning_totals.c.revenue)
        .outerjoin(earning_totals, earning_totals.c.content_item_id == ContentItem.id)
        .filter(ContentItem.owner_id == current_user.id)
        .order_by(ContentItem.id.desc())
        .limit(25)
        .all()
    )
    return DashboardOverview(
        summary=EarningsSummary(**summary_data),
        profit_share=ProfitShareBreakdown(**breakdown),
        suggestions=suggestions,
        programs=program_breakdown(db, current_user.id),
        posts=[
            PostEarnings(
                id=post.id,
                title=post.title,
                status=post.status,
                keyword=post.keyword,
                revenue=float(revenue or 0),
                published_url=post.published_url,
            )
            for post, revenue in posts
        ],
    )


@router.get("/programs", response_model=MultiProgramDashboard)
def multi_program_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MultiProgramDashboard:
    programs = program_breakdown(db, current_user.id)
    return MultiProgramDashboard(
        total_revenue=round(sum(program.revenue for program in programs), 2),
        programs=programs,
    )


def program_breakdown(db: Session, owner_id: int) -> list[ProgramEarningsBreakdown]:
    revenue = func.sum(EarningEvent.amount)
    rows = (
        EarningsTracker()
        .owned_usd(db, owner_id)
        .with_entities(
            EarningEvent.network,
            func.count(EarningEvent.id).label("events"),
            revenue.label("revenue"),
        )
        .group_by(EarningEvent.network)
        .order_by(revenue.desc(), EarningEvent.network)
        .all()
    )
    return [
        ProgramEarningsBreakdown(
            network=row.network, events=row.events, revenue=float(row.revenue or 0)
        )
        for row in rows
    ]


@router.post("/ad-optimizer", response_model=AdOptimizerResponse)
def ad_revenue_optimizer(
    payload: AdOptimizerRequest,
    _: User = Depends(get_current_user),
) -> AdOptimizerResponse:
    optimizer = AdRevenueOptimizer()
    result = optimizer.optimize(
        ga4_sessions=payload.ga4_sessions,
        pageviews=payload.pageviews,
        adsense_revenue=payload.adsense_revenue,
        adsense_ctr=payload.adsense_ctr,
    )
    return AdOptimizerResponse(**result)
