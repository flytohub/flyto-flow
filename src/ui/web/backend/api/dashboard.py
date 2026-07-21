"""
Dashboard API Routes

Provides dashboard statistics and analytics endpoints.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)
from pydantic import BaseModel, Field

from api.auth import get_current_user
from gateway.providers.hub import get_data_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# =============================================================================
# Response Models
# =============================================================================


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    sales: int = Field(default=0, description="Total number of sales")
    revenue: float = Field(default=0, description="Total revenue in dollars (after fees)")
    published: int = Field(default=0, description="Number of published templates")
    active_keys: int = Field(default=0, description="Number of active invite keys")


class TrendDataPoint(BaseModel):
    """Single trend data point"""
    day: str = Field(..., description="Day of week (e.g., 'Mon')")
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    sales: int = Field(default=0, description="Number of sales")
    revenue: float = Field(default=0, description="Revenue in dollars")


class SalesTrendResponse(BaseModel):
    """Sales trend response"""
    ok: bool = True
    trend: List[TrendDataPoint] = Field(default_factory=list)
    total_sales: int = 0
    total_revenue: float = 0
    sales_trend_percent: int = 0
    revenue_trend_percent: int = 0


class ActivityItem(BaseModel):
    """Recent activity item (sale or execution)"""
    id: str
    type: str = "sale"  # "sale" or "execution"
    template_name: str = "Unknown Template"
    # Sale fields
    buyer_email: Optional[str] = None
    amount: float = 0
    earnings: float = 0
    currency: str = "usd"
    created_at: Optional[str] = None
    purchased_at: Optional[str] = None
    # Execution fields
    status: Optional[str] = None  # "success", "failed", "running"
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    execution_time: Optional[float] = None  # seconds
    error_message: Optional[str] = None


class RecentActivityResponse(BaseModel):
    """Recent activity response"""
    ok: bool = True
    activities: List[ActivityItem] = Field(default_factory=list)


class PurchaseItem(BaseModel):
    """Purchase item"""
    id: str
    template_id: str
    template_name: str = "Unknown Template"
    template_icon: Optional[str] = None
    amount: float = 0
    currency: str = "usd"
    purchased_at: Optional[str] = None


class MyPurchasesResponse(BaseModel):
    """My purchases response"""
    ok: bool = True
    purchases: List[PurchaseItem] = Field(default_factory=list)
    total_spent: float = 0
    count: int = 0
    free_count: int = 0


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    current_user: dict = Depends(get_current_user),
):
    """Get dashboard statistics"""
    provider = get_data_provider()
    user_id = current_user["id"]

    # Get stats from data provider
    try:
        stats = await provider.dashboard.get_stats(user_id)
        return DashboardStats(
            sales=stats.get("sales", 0),
            revenue=stats.get("revenue", 0),
            published=stats.get("published", 0),
            active_keys=stats.get("active_keys", 0),
        )
    except Exception as e:
        logger.error(f"Failed to get dashboard stats: {e}")
        return DashboardStats()


@router.get("/sales-trend", response_model=SalesTrendResponse)
async def get_sales_trend(
    days: int = Query(7, ge=1, le=90, description="Number of days to fetch"),
    current_user: dict = Depends(get_current_user),
):
    """Get sales trend for chart"""
    provider = get_data_provider()
    user_id = current_user["id"]

    try:
        trend_data = await provider.dashboard.get_sales_trend(user_id, days)

        trend = [
            TrendDataPoint(
                day=item.get("day", ""),
                date=item.get("date", ""),
                sales=item.get("sales", 0),
                revenue=item.get("revenue", 0),
            )
            for item in trend_data.get("trend", [])
        ]

        return SalesTrendResponse(
            ok=True,
            trend=trend,
            total_sales=trend_data.get("total_sales", 0),
            total_revenue=trend_data.get("total_revenue", 0),
            sales_trend_percent=trend_data.get("sales_trend_percent", 0),
            revenue_trend_percent=trend_data.get("revenue_trend_percent", 0),
        )
    except Exception as e:
        logger.error(f"Failed to get sales trend: {e}")
        # Return empty trend for the requested days
        trend = []
        for i in range(days):
            date = _utc_now() - timedelta(days=days - 1 - i)
            trend.append(TrendDataPoint(
                day=date.strftime("%a"),
                date=date.strftime("%Y-%m-%d"),
                sales=0,
                revenue=0,
            ))
        return SalesTrendResponse(ok=False, trend=trend)


@router.get("/recent-activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50, description="Number of activities to return"),
    current_user: dict = Depends(get_current_user),
):
    """Get recent activity (sales, etc.)"""
    provider = get_data_provider()
    user_id = current_user["id"]

    try:
        activities_data = await provider.dashboard.get_recent_activity(user_id, limit)

        activities = [
            ActivityItem(
                id=item.get("id", ""),
                type=item.get("type", "sale"),
                template_name=item.get("template_name", "Unknown Template"),
                # Sale fields
                buyer_email=item.get("buyer_email"),
                amount=item.get("amount", 0),
                earnings=item.get("earnings", 0),
                currency=item.get("currency", "usd"),
                created_at=item.get("created_at"),
                purchased_at=item.get("purchased_at"),
                # Execution fields
                status=item.get("status"),
                started_at=item.get("started_at"),
                completed_at=item.get("completed_at"),
                execution_time=item.get("execution_time"),
                error_message=item.get("error_message"),
            )
            for item in activities_data.get("activities", [])
        ]

        return RecentActivityResponse(ok=True, activities=activities)
    except Exception as e:
        logger.error(f"Failed to get recent activity: {e}")
        return RecentActivityResponse(ok=False, activities=[])


class RecentTemplateItem(BaseModel):
    """Recent template item"""
    id: str
    name: str = "Untitled Template"
    icon: Optional[str] = None
    category: Optional[str] = None
    updated_at: Optional[str] = None


class RecentTemplatesResponse(BaseModel):
    """Recent templates response"""
    ok: bool = True
    templates: List[RecentTemplateItem] = Field(default_factory=list)


@router.get("/recent-templates", response_model=RecentTemplatesResponse)
async def get_recent_templates(
    limit: int = Query(10, ge=1, le=50, description="Number of templates to return"),
    current_user: dict = Depends(get_current_user),
):
    """Get user's recently updated templates"""
    provider = get_data_provider()
    user_id = current_user["id"]

    try:
        templates_data = await provider.dashboard.get_recent_templates(user_id, limit)

        templates = [
            RecentTemplateItem(
                id=item.get("id", ""),
                name=item.get("name", "Untitled Template"),
                icon=item.get("icon"),
                category=item.get("category"),
                updated_at=item.get("updated_at"),
            )
            for item in templates_data.get("templates", [])
        ]

        return RecentTemplatesResponse(ok=True, templates=templates)
    except Exception as e:
        logger.error(f"Failed to get recent templates: {e}")
        return RecentTemplatesResponse(ok=False, templates=[])


@router.get("/my-purchases", response_model=MyPurchasesResponse)
async def get_my_purchases(
    limit: int = Query(10, ge=1, le=50, description="Number of purchases to return"),
    current_user: dict = Depends(get_current_user),
):
    """Get user's purchase history"""
    provider = get_data_provider()
    user_id = current_user["id"]

    try:
        purchases_data = await provider.dashboard.get_my_purchases(user_id, limit)

        purchases = [
            PurchaseItem(
                id=item.get("id", ""),
                template_id=item.get("template_id", ""),
                template_name=item.get("template_name", "Unknown Template"),
                template_icon=item.get("template_icon"),
                amount=item.get("amount", 0),
                currency=item.get("currency", "usd"),
                purchased_at=item.get("purchased_at"),
            )
            for item in purchases_data.get("purchases", [])
        ]

        return MyPurchasesResponse(
            ok=True,
            purchases=purchases,
            total_spent=purchases_data.get("total_spent", 0),
            count=purchases_data.get("count", 0),
            free_count=purchases_data.get("free_count", 0),
        )
    except Exception as e:
        logger.error(f"Failed to get purchases: {e}")
        return MyPurchasesResponse(ok=False, purchases=[])
