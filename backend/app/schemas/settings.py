from pydantic import BaseModel


class SettingsOut(BaseModel):
    ai_provider: str
    ai_mode: str
    ai_key_set: bool
    telegram_bot_token_set: bool
    telegram_webhook_secret_set: bool
