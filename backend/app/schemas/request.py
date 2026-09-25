from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Intent, MessageDirection, MessageSource, RequestStatus
from app.schemas.client import ClientOut


class RequestCreateIn(BaseModel):
    client_id: int
    text: str = Field(min_length=1, max_length=4000)


class RequestUpdateIn(BaseModel):
    status: RequestStatus | None = None
    service_id: int | None = None
    preferred_date: str | None = Field(default=None, max_length=100)
    preferred_time: str | None = Field(default=None, max_length=100)
    summary: str | None = Field(default=None, max_length=2000)
    requires_manual_review: bool | None = None


class AIAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intent: Intent
    confidence: float
    service_name: str | None = None
    preferred_date: str | None = None
    preferred_time: str | None = None
    requires_manual_review: bool
    created_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    direction: MessageDirection
    source: MessageSource
    text: str
    telegram_update_id: int | None = None
    created_at: datetime


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    old_status: RequestStatus | None = None
    new_status: RequestStatus
    changed_by_user_id: int | None = None
    created_at: datetime


class RequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    client: ClientOut | None = None
    service_id: int | None = None
    service_name: str | None = None
    status: RequestStatus
    source: MessageSource
    summary: str | None = None
    preferred_date: str | None = None
    preferred_time: str | None = None
    requires_manual_review: bool
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime
    latest_ai: AIAnalysisOut | None = None


class RequestDetailOut(RequestOut):
    messages: list[MessageOut] = Field(default_factory=list)
    ai_analyses: list[AIAnalysisOut] = Field(default_factory=list)
    status_history: list[StatusHistoryOut] = Field(default_factory=list)


class ClientDetailOut(BaseModel):
    client: ClientOut
    requests: list[RequestOut] = Field(default_factory=list)
