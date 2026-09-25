from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import MessageDirection, MessageSource, RequestStatus


class ClientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone: str | None = None
    email: str | None = None
    telegram_user_id: int | None = None
    notes: str | None = None
    created_at: datetime
