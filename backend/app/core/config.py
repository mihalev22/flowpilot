from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "FlowPilot"
    DATABASE_URL: str = "sqlite:///./flowpilot.db"
    JWT_SECRET: str = "change-me"
    JWT_EXPIRE_MINUTES: int = 60
    AI_MODE: str = "mock"
    AI_PROVIDER: str = "mock"
    AI_API_KEY: str = ""
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def provider_name(self) -> str:
        if self.AI_MODE == "mock" or self.AI_PROVIDER == "mock":
            return "mock"
        if self.AI_PROVIDER in ("openai", "qwen"):
            return self.AI_PROVIDER
        return "mock"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_ai_config(settings: Settings) -> None:
    if settings.AI_PROVIDER not in ("mock", "openai", "qwen"):
        raise RuntimeError(f"Неизвестный AI_PROVIDER: {settings.AI_PROVIDER}")
    if settings.provider_name in ("openai", "qwen") and not settings.AI_API_KEY:
        raise RuntimeError(f"AI_PROVIDER={settings.provider_name} требует AI_API_KEY")
