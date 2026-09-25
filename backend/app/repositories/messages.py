from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Message
from app.models.enums import MessageDirection, MessageSource


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        business_id: int,
        client_id: int,
        direction: MessageDirection,
        source: MessageSource,
        text: str,
        request_id: int | None = None,
        telegram_update_id: int | None = None,
    ) -> Message:
        message = Message(
            business_id=business_id,
            client_id=client_id,
            request_id=request_id,
            direction=direction,
            source=source,
            text=text,
            telegram_update_id=telegram_update_id,
        )
        self.db.add(message)
        self.db.flush()
        return message

    def exists_telegram_update(self, business_id: int, telegram_update_id: int) -> bool:
        stmt = select(func.count(Message.id)).where(
            Message.business_id == business_id,
            Message.telegram_update_id == telegram_update_id,
        )
        return (self.db.scalar(stmt) or 0) > 0

    def list_by_request(self, request_id: int) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.request_id == request_id)
            .order_by(Message.created_at, Message.id)
        )
        return list(self.db.scalars(stmt))
