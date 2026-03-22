from pydantic import BaseModel, ConfigDict, Field


class EarningCreate(BaseModel):
    network: str
    amount: float = Field(gt=0)
    currency: str = "USD"
    content_item_id: int


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


class DashboardOverview(BaseModel):
    summary: EarningsSummary
    profit_share: ProfitShareBreakdown
    suggestions: list[str]
