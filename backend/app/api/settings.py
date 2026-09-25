from fastapi import APIRouter, Depends

from app.api.deps import require_admin
from app.core.config import Settings, get_settings
from app.models import User
from app.schemas.settings import SettingsOut

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("", response_model=SettingsOut)
def get_settings_status(
    user: User = Depends(require_admin),
    settings: Settings = Depends(get_settings),
) -> SettingsOut:
    return SettingsOut(
        ai_provider=settings.provider_name,
        ai_mode=settings.AI_MODE,
        ai_key_set=bool(settings.AI_API_KEY),
        telegram_bot_token_set=bool(settings.TELEGRAM_BOT_TOKEN),
        telegram_webhook_secret_set=bool(settings.TELEGRAM_WEBHOOK_SECRET),
    )
