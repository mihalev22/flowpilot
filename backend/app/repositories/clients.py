from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client


class ClientRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        business_id: int,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        telegram_user_id: int | None = None,
    ) -> Client:
        client = Client(
            business_id=business_id,
            name=name,
            phone=phone,
            email=email,
            telegram_user_id=telegram_user_id,
        )
        self.db.add(client)
        self.db.flush()
        return client

    def get(self, business_id: int, client_id: int) -> Client | None:
        stmt = select(Client).where(Client.business_id == business_id, Client.id == client_id)
        return self.db.scalars(stmt).first()

    def get_by_telegram_id(self, business_id: int, telegram_user_id: int) -> Client | None:
        stmt = select(Client).where(
            Client.business_id == business_id, Client.telegram_user_id == telegram_user_id
        )
        return self.db.scalars(stmt).first()

    def list(self, business_id: int, limit: int = 500) -> list[Client]:
        stmt = (
            select(Client)
            .where(Client.business_id == business_id)
            .order_by(Client.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt))
