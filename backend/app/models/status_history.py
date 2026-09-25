from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import RequestStatus


class RequestStatusHistory(Base):
    __tablename__ = "request_status_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("client_requests.id"), nullable=False, index=True)
    old_status: Mapped[RequestStatus | None] = mapped_column(
        Enum(RequestStatus, name="old_request_status", native_enum=False, create_constraint=True, length=20,
             values_callable=lambda e: [m.value for m in e]),
        nullable=True,
    )
    new_status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="request_status", native_enum=False, create_constraint=True, length=20,
             values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    changed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
