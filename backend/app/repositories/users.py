from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Business, User
from app.models.enums import UserRole


class BusinessRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str) -> Business:
        business = Business(name=name)
        self.db.add(business)
        self.db.flush()
        return business

    def get(self, business_id: int) -> Business | None:
        return self.db.get(Business, business_id)

    def get_first(self) -> Business | None:
        return self.db.scalars(select(Business).order_by(Business.id)).first()


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        business_id: int,
        email: str,
        password_hash: str,
        full_name: str,
        role: UserRole,
    ) -> User:
        user = User(
            business_id=business_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalars(select(User).where(User.email == email)).first()
