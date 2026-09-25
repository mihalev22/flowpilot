from fastapi import APIRouter, Depends

from app.api.deps import get_analytics_service, require_admin
from app.models import User
from app.schemas.dashboard import DashboardStatsOut
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsOut)
def stats(
    user: User = Depends(require_admin),
    service: AnalyticsService = Depends(get_analytics_service),
) -> DashboardStatsOut:
    return service.stats(user.business_id)
