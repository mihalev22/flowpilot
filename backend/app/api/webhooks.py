import hmac

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_telegram_service
from app.core.config import Settings, get_settings
from app.core.exceptions import ForbiddenError
from app.schemas.telegram import TelegramWebhookIn
from app.services.telegram import TelegramService

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/telegram")
def telegram_webhook(
    payload: TelegramWebhookIn,
    request: Request,
    settings: Settings = Depends(get_settings),
    service: TelegramService = Depends(get_telegram_service),
) -> dict:
    secret = request.headers.get("X-Telegram-Secret", "")
    if not settings.TELEGRAM_WEBHOOK_SECRET or not hmac.compare_digest(
        secret, settings.TELEGRAM_WEBHOOK_SECRET
    ):
        raise ForbiddenError("Недействительный секрет вебхука")
    created = service.process_update(payload)
    if created is None:
        return {"detail": "Обновление обработано без создания заявки", "request_id": None}
    return {"detail": "Обновление обработано", "request_id": created.id}
