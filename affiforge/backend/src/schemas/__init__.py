"""Pydantic schema package."""

from .auth import LoginRequest, TokenResponse
from .billing import (
	CheckoutSessionRequest,
	CheckoutSessionResponse,
	ProfitShareInvoiceRequest,
	ProfitShareInvoiceResponse,
	ProfitShareToggleRequest,
)
from .content import ContentCreate, ContentRead
from .earnings import (
	AdOptimizerRequest,
	AdOptimizerResponse,
	DashboardOverview,
	EarningCreate,
	EarningRead,
	EarningsSummary,
	MultiProgramDashboard,
	OptimizationSuggestions,
	ProgramEarningsBreakdown,
	ProfitShareBreakdown,
)
from .generator import (
	ClusterGenerateRequest,
	ClusterGenerateResponse,
	GeneratePostRequest,
	PublishPostRequest,
	RedditScanRequest,
	RedditScanResponse,
)
from .scan import ScanCreate, ScanRead
from .site import SiteCreate, SiteRead
from .user import UserCreate, UserRead

__all__ = [
	"UserCreate",
	"UserRead",
	"LoginRequest",
	"TokenResponse",
	"ContentCreate",
	"ContentRead",
	"SiteCreate",
	"SiteRead",
	"ScanCreate",
	"ScanRead",
	"EarningCreate",
	"EarningRead",
	"EarningsSummary",
	"ProfitShareBreakdown",
	"OptimizationSuggestions",
	"DashboardOverview",
	"ProgramEarningsBreakdown",
	"MultiProgramDashboard",
	"AdOptimizerRequest",
	"AdOptimizerResponse",
	"RedditScanRequest",
	"RedditScanResponse",
	"ClusterGenerateRequest",
	"ClusterGenerateResponse",
	"GeneratePostRequest",
	"PublishPostRequest",
	"CheckoutSessionRequest",
	"CheckoutSessionResponse",
	"ProfitShareToggleRequest",
	"ProfitShareInvoiceRequest",
	"ProfitShareInvoiceResponse",
]
