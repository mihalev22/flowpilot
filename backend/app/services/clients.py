from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models import Client
from app.repositories.clients import ClientRepository
from app.schemas.telegram import TelegramUserIn


class ClientService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ClientRepository(db)

    def get(self, business_id: int, client_id: int) -> Client:
        client = self.repo.get(business_id, client_id)
        if client is None:
            raise NotFoundError("Клиент не найден")
        return client

    def list(self, business_id: int, search: str | None = None) -> list[Client]:
        clients = self.repo.list(business_id)
        if search:
            query = search.strip().lower()
            clients = [
                client
                for client in clients
                if query in client.name.lower() or (client.phone and query in client.phone.lower())
            ]
        return clients

    def get_or_create_telegram(self, business_id: int, tg_user: TelegramUserIn) -> Client:
        existing = self.repo.get_by_telegram_id(business_id, tg_user.id)
        if existing is not None:
            return existing
        name = f"{tg_user.first_name} {tg_user.last_name}".strip()
        if not name:
            name = tg_user.username or f"Telegram {tg_user.id}"
        return self.repo.create(business_id=business_id, name=name, telegram_user_id=tg_user.id)
