from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import MessageSource, RequestStatus


class Request(Base):
    __tablename__ = "client_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    service_id: Mapped[int | None] = mapped_column(ForeignKey("services.id"), nullable=True)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status", native_enum=False, create_constraint=True, length=20,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=RequestStatus.NEW,
        index=True,
    )
    source: Mapped[MessageSource] = mapped_column(
        Enum(MessageSource, name="request_source", native_enum=False, create_constraint=True, length=20,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=MessageSource.WEB,
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    preferred_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_time: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    client = relationship("Client", lazy="selectin")
    service = relationship("Service", lazy="selectin")
    messages = relationship("Message", order_by="Message.created_at", lazy="selectin", cascade="all, delete-orphan")
    ai_analyses = relationship(
        "AIAnalysis", order_by="AIAnalysis.created_at.desc()", lazy="selectin", cascade="all, delete-orphan"
    )
    status_history = relationship(
        "RequestStatusHistory", order_by="RequestStatusHistory.created_at", lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def service_name(self) -> str | None:
        return self.service.name if self.service else None

    @property
    def latest_ai(self):
        return self.ai_analyses[0] if self.ai_analyses else None
