from sqlalchemy.orm import Session

from app.repositories.services import ServiceRepository


class CatalogService:
    def __init__(self, db: Session):
        self.repo = ServiceRepository(db)

    def list(self, business_id: int):
        return self.repo.list(business_id)
