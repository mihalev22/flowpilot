from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import MessageDirection, MessageSource


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("business_id", "telegram_update_id", name="uq_messages_business_telegram_update"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    request_id: Mapped[int | None] = mapped_column(ForeignKey("client_requests.id"), nullable=True, index=True)
    direction: Mapped[MessageDirection] = mapped_column(
        Enum(MessageDirection, name="message_direction", native_enum=False, create_constraint=True, length=10,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MessageDirection.IN,
    )
    source: Mapped[MessageSource] = mapped_column(
        Enum(MessageSource, name="message_source", native_enum=False, create_constraint=True, length=20,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MessageSource.WEB,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    telegram_update_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
