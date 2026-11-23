from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EarningCreate(BaseModel):
    network: str = Field(min_length=1, max_length=120)
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    currency: Literal["USD"] = "USD"
    content_item_id: int = Field(gt=0)
    entry_key: UUID | None = None


class EarningRead(BaseModel):
    id: int
    network: str
    amount: float
    currency: str
    content_item_id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class EarningsSummary(BaseModel):
    posts_count: int
    revenue: float
    earnings_count: int
    epc: float


class ProfitShareBreakdown(BaseModel):
    enabled: bool
    total_revenue: float
    platform_share: float
    user_share: float
    ratio: float


class OptimizationSuggestions(BaseModel):
    suggestions: list[str]


class ProgramEarningsBreakdown(BaseModel):
    network: str
    revenue: float
    events: int


class PostEarnings(BaseModel):
    id: int
    title: str
    status: str
    keyword: str | None
    revenue: float
    published_url: str | None


class DashboardOverview(BaseModel):
    summary: EarningsSummary
    profit_share: ProfitShareBreakdown
    suggestions: list[str]
    programs: list[ProgramEarningsBreakdown]
    posts: list[PostEarnings]


class MultiProgramDashboard(BaseModel):
    total_revenue: float
    programs: list[ProgramEarningsBreakdown]


class AdOptimizerRequest(BaseModel):
    ga4_sessions: int = Field(ge=0)
    pageviews: int = Field(ge=0)
    adsense_revenue: float = Field(ge=0)
    adsense_ctr: float = Field(ge=0)


class AdOptimizerResponse(BaseModel):
    rpm: float
    session_depth: float
    projected_rpm_uplift: float
    suggestions: list[str]
