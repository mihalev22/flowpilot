import datetime as dt

from sqlalchemy.orm import Session

from app.repositories.requests import RequestRepository
from app.schemas.dashboard import (
    DashboardStatsOut,
    DayCountOut,
    ServiceCountOut,
    SourceCountOut,
    StatusCountsOut,
)
from app.schemas.request import RequestOut


class AnalyticsService:
    def __init__(self, db: Session):
        self.repo = RequestRepository(db)

    def stats(self, business_id: int) -> DashboardStatsOut:
        by_status = self.repo.counts_by_status(business_id)
        counts_by_day = self.repo.counts_by_day(business_id)
        today = dt.date.today()
        by_day = [
            DayCountOut(date=(today - dt.timedelta(days=offset)).isoformat(),
                        count=counts_by_day.get((today - dt.timedelta(days=offset)).isoformat(), 0))
            for offset in range(13, -1, -1)
        ]
        return DashboardStatsOut(
            total=self.repo.count(business_id),
            status_counts=StatusCountsOut(
                new=by_status.get("NEW", 0),
                in_progress=by_status.get("IN_PROGRESS", 0),
                confirmed=by_status.get("CONFIRMED", 0),
                completed=by_status.get("COMPLETED", 0),
                cancelled=by_status.get("CANCELLED", 0),
            ),
            requires_review=self.repo.count(business_id, requires_review=True),
            by_day=by_day,
            by_source=[
                SourceCountOut(source=source, count=count)
                for source, count in self.repo.counts_by_source(business_id).items()
            ],
            top_services=[
                ServiceCountOut(service_name=name, count=count)
                for name, count in self.repo.top_services(business_id)
            ],
            recent_requests=[RequestOut.model_validate(r) for r in self.repo.list(business_id, limit=5)],
        )
