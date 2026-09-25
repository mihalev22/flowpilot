from pydantic import BaseModel, Field

from app.models.enums import MessageSource
from app.schemas.request import RequestOut


class StatusCountsOut(BaseModel):
    new: int = 0
    in_progress: int = 0
    confirmed: int = 0
    completed: int = 0
    cancelled: int = 0


class DayCountOut(BaseModel):
    date: str
    count: int


class SourceCountOut(BaseModel):
    source: MessageSource
    count: int


class ServiceCountOut(BaseModel):
    service_name: str
    count: int


class DashboardStatsOut(BaseModel):
    total: int
    status_counts: StatusCountsOut
    requires_review: int
    by_day: list[DayCountOut] = Field(default_factory=list)
    by_source: list[SourceCountOut] = Field(default_factory=list)
    top_services: list[ServiceCountOut] = Field(default_factory=list)
    recent_requests: list[RequestOut] = Field(default_factory=list)
