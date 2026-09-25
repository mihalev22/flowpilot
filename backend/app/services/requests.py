from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Request, User
from app.models.enums import MessageDirection, MessageSource, RequestStatus
from app.repositories.clients import ClientRepository
from app.repositories.messages import MessageRepository
from app.repositories.requests import (
    AIAnalysisRepository,
    RequestRepository,
    RequestStatusHistoryRepository,
)
from app.repositories.services import ServiceRepository
from app.services.ai import AIAnalysisService


class RequestService:
    def __init__(self, db: Session, ai_service: AIAnalysisService):
        self.db = db
        self.ai_service = ai_service
        self.request_repo = RequestRepository(db)
        self.message_repo = MessageRepository(db)
        self.ai_repo = AIAnalysisRepository(db)
        self.history_repo = RequestStatusHistoryRepository(db)
        self.service_repo = ServiceRepository(db)
        self.client_repo = ClientRepository(db)

    def create_from_text(
        self,
        *,
        business_id: int,
        client_id: int,
        text: str,
        source: MessageSource,
        created_by_user_id: int | None = None,
        telegram_update_id: int | None = None,
    ) -> Request:
        client = self.client_repo.get(business_id, client_id)
        if client is None:
            raise NotFoundError("Клиент не найден")
        result = self.ai_service.analyze_safe(text)
        service = None
        if result.service_name:
            service = self.service_repo.get_by_name(business_id, result.service_name)
        requires_review = result.confidence < 0.60 or result.requires_manual_review
        request = self.request_repo.create(
            business_id=business_id,
            client_id=client_id,
            service_id=service.id if service else None,
            status=RequestStatus.NEW,
            source=source,
            summary=text[:200],
            preferred_date=result.preferred_date,
            preferred_time=result.preferred_time,
            requires_manual_review=requires_review,
            created_by_user_id=created_by_user_id,
        )
        self.message_repo.create(
            business_id=business_id,
            client_id=client_id,
            direction=MessageDirection.IN,
            source=source,
            text=text,
            request_id=request.id,
            telegram_update_id=telegram_update_id,
        )
        self.ai_repo.create(request_id=request.id, result=result)
        self.db.commit()
        self.db.refresh(request)
        return request

    def get(self, business_id: int, request_id: int) -> Request:
        request = self.request_repo.get(business_id, request_id)
        if request is None:
            raise NotFoundError("Заявка не найдена")
        return request

    def list(
        self,
        business_id: int,
        status: RequestStatus | None = None,
        requires_review: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Request]:
        return self.request_repo.list(
            business_id, status=status, requires_review=requires_review, limit=limit, offset=offset
        )

    def list_by_client(self, business_id: int, client_id: int) -> list[Request]:
        return self.request_repo.list_by_client(business_id, client_id)

    def update(self, business_id: int, request_id: int, fields: dict, user: User) -> Request:
        request = self.get(business_id, request_id)
        if "status" in fields and fields["status"] is not None:
            new_status = fields["status"]
            if new_status != request.status:
                self.history_repo.create(request.id, request.status, new_status, user.id)
                request.status = new_status
        if "service_id" in fields:
            service_id = fields["service_id"]
            if service_id is not None:
                service = self.service_repo.get(business_id, service_id)
                if service is None:
                    raise NotFoundError("Услуга не найдена")
            request.service_id = service_id
        for attr in ("preferred_date", "preferred_time", "summary", "requires_manual_review"):
            if attr in fields:
                setattr(request, attr, fields[attr])
        self.db.commit()
        self.db.refresh(request)
        return request
