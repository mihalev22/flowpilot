from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AIAnalysis, Request, RequestStatusHistory, Service
from app.models.enums import MessageSource, RequestStatus
from app.schemas.ai_result import AIResult


def _enum_value(value) -> str:
    if hasattr(value, "value"):
        return value.value
    return str(value)


class RequestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        business_id: int,
        client_id: int,
        status: RequestStatus,
        source: MessageSource,
        service_id: int | None = None,
        summary: str | None = None,
        preferred_date: str | None = None,
        preferred_time: str | None = None,
        requires_manual_review: bool = False,
        created_by_user_id: int | None = None,
    ) -> Request:
        request = Request(
            business_id=business_id,
            client_id=client_id,
            service_id=service_id,
            status=status,
            source=source,
            summary=summary,
            preferred_date=preferred_date,
            preferred_time=preferred_time,
            requires_manual_review=requires_manual_review,
            created_by_user_id=created_by_user_id,
        )
        self.db.add(request)
        self.db.flush()
        return request

    def get(self, business_id: int, request_id: int) -> Request | None:
        stmt = select(Request).where(Request.business_id == business_id, Request.id == request_id)
        return self.db.scalars(stmt).first()

    def list(
        self,
        business_id: int,
        status: RequestStatus | None = None,
        requires_review: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Request]:
        stmt = select(Request).where(Request.business_id == business_id)
        if status is not None:
            stmt = stmt.where(Request.status == status)
        if requires_review is not None:
            stmt = stmt.where(Request.requires_manual_review == requires_review)
        stmt = stmt.order_by(Request.created_at.desc()).limit(limit).offset(offset)
        return list(self.db.scalars(stmt))

    def list_by_client(self, business_id: int, client_id: int) -> list[Request]:
        stmt = (
            select(Request)
            .where(Request.business_id == business_id, Request.client_id == client_id)
            .order_by(Request.created_at.desc())
        )
        return list(self.db.scalars(stmt))

    def count(
        self,
        business_id: int,
        status: RequestStatus | None = None,
        requires_review: bool | None = None,
    ) -> int:
        stmt = select(func.count(Request.id)).where(Request.business_id == business_id)
        if status is not None:
            stmt = stmt.where(Request.status == status)
        if requires_review is not None:
            stmt = stmt.where(Request.requires_manual_review == requires_review)
        return self.db.scalar(stmt) or 0

    def counts_by_status(self, business_id: int) -> dict[str, int]:
        stmt = (
            select(Request.status, func.count(Request.id))
            .where(Request.business_id == business_id)
            .group_by(Request.status)
        )
        return {_enum_value(status): count for status, count in self.db.execute(stmt).all()}

    def counts_by_day(self, business_id: int, days: int = 14) -> dict[str, int]:
        day = func.date(Request.created_at)
        stmt = (
            select(day, func.count(Request.id))
            .where(Request.business_id == business_id)
            .group_by(day)
        )
        return {str(value)[:10]: count for value, count in self.db.execute(stmt).all()}

    def counts_by_source(self, business_id: int) -> dict[str, int]:
        stmt = (
            select(Request.source, func.count(Request.id))
            .where(Request.business_id == business_id)
            .group_by(Request.source)
        )
        return {_enum_value(source): count for source, count in self.db.execute(stmt).all()}

    def top_services(self, business_id: int, limit: int = 5) -> list[tuple[str, int]]:
        stmt = (
            select(Service.name, func.count(Request.id))
            .join(Service, Request.service_id == Service.id)
            .where(Request.business_id == business_id)
            .group_by(Service.name)
            .order_by(func.count(Request.id).desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).all())


class AIAnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, request_id: int, result: AIResult) -> AIAnalysis:
        analysis = AIAnalysis(
            request_id=request_id,
            intent=result.intent,
            confidence=result.confidence,
            service_name=result.service_name,
            preferred_date=result.preferred_date,
            preferred_time=result.preferred_time,
            requires_manual_review=result.requires_manual_review,
        )
        self.db.add(analysis)
        self.db.flush()
        return analysis

    def get_latest(self, request_id: int) -> AIAnalysis | None:
        stmt = (
            select(AIAnalysis)
            .where(AIAnalysis.request_id == request_id)
            .order_by(AIAnalysis.created_at.desc(), AIAnalysis.id.desc())
        )
        return self.db.scalars(stmt).first()


class RequestStatusHistoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        request_id: int,
        old_status: RequestStatus | None,
        new_status: RequestStatus,
        changed_by_user_id: int | None = None,
    ) -> RequestStatusHistory:
        record = RequestStatusHistory(
            request_id=request_id,
            old_status=old_status,
            new_status=new_status,
            changed_by_user_id=changed_by_user_id,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def list_by_request(self, request_id: int) -> list[RequestStatusHistory]:
        stmt = (
            select(RequestStatusHistory)
            .where(RequestStatusHistory.request_id == request_id)
            .order_by(RequestStatusHistory.created_at, RequestStatusHistory.id)
        )
        return list(self.db.scalars(stmt))
