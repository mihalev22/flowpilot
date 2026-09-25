from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import Intent


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("client_requests.id"), nullable=False, index=True)
    intent: Mapped[Intent] = mapped_column(
        Enum(Intent, name="ai_intent", native_enum=False, create_constraint=True, length=30,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    service_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    preferred_date: Mapped[str | None] = mapped_column(String(100), nullable=True)
    preferred_time: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requires_manual_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
