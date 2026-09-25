from pydantic import BaseModel, Field

from app.models.enums import Intent


class AIResult(BaseModel):
    intent: Intent
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    service_name: str | None = None
    preferred_date: str | None = None
    preferred_time: str | None = None
    requires_manual_review: bool = False
