from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Service


class ServiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        business_id: int,
        name: str,
        duration_minutes: int | None = None,
        price: float | None = None,
    ) -> Service:
        service = Service(
            business_id=business_id,
            name=name,
            duration_minutes=duration_minutes,
            price=price,
        )
        self.db.add(service)
        self.db.flush()
        return service

    def get(self, business_id: int, service_id: int) -> Service | None:
        stmt = select(Service).where(Service.business_id == business_id, Service.id == service_id)
        return self.db.scalars(stmt).first()

    def list(self, business_id: int) -> list[Service]:
        stmt = select(Service).where(Service.business_id == business_id).order_by(Service.name)
        return list(self.db.scalars(stmt))

    def get_by_name(self, business_id: int, name: str) -> Service | None:
        for service in self.list(business_id):
            if service.name.lower() == name.lower():
                return service
        return None
