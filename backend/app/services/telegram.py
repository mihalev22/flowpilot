from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Request
from app.models.enums import MessageSource
from app.repositories.messages import MessageRepository
from app.repositories.users import BusinessRepository
from app.schemas.telegram import TelegramWebhookIn
from app.services.clients import ClientService
from app.services.requests import RequestService


class TelegramService:
    def __init__(self, db: Session, request_service: RequestService, client_service: ClientService):
        self.db = db
        self.request_service = request_service
        self.client_service = client_service
        self.business_repo = BusinessRepository(db)
        self.message_repo = MessageRepository(db)

    def process_update(self, payload: TelegramWebhookIn) -> Request | None:
        business = self.business_repo.get_first()
        if business is None:
            raise NotFoundError("Бизнес не найден — сначала зарегистрируйте аккаунт")
        if payload.message is None:
            return None
        if self.message_repo.exists_telegram_update(business.id, payload.update_id):
            return None
        client = self.client_service.get_or_create_telegram(business.id, payload.message.from_)
        return self.request_service.create_from_text(
            business_id=business.id,
            client_id=client.id,
            text=payload.message.text,
            source=MessageSource.TELEGRAM,
            telegram_update_id=payload.update_id,
        )
