from pydantic import BaseModel, ConfigDict, Field


class TelegramUserIn(BaseModel):
    id: int
    first_name: str = ""
    last_name: str = ""
    username: str = ""


class TelegramMessageIn(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message_id: int
    from_: TelegramUserIn = Field(validation_alias="from")
    text: str = Field(min_length=1, max_length=4000)


class TelegramWebhookIn(BaseModel):
    update_id: int
    message: TelegramMessageIn | None = None
