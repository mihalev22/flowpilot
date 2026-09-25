from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, ConflictError
from app.core.security import hash_password, verify_password
from app.models import User
from app.models.enums import UserRole
from app.repositories.users import BusinessRepository, UserRepository
from app.schemas.auth import LoginIn, RegisterIn


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.business_repo = BusinessRepository(db)

    def register(self, data: RegisterIn) -> User:
        email = data.email.lower()
        if self.user_repo.get_by_email(email) is not None:
            raise ConflictError("Пользователь с таким email уже зарегистрирован")
        business = self.business_repo.create(data.business_name)
        user = self.user_repo.create(
            business_id=business.id,
            email=email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.ADMIN,
        )
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("Пользователь с таким email уже зарегистрирован") from exc
        self.db.refresh(user)
        return user

    def login(self, data: LoginIn) -> User:
        user = self.user_repo.get_by_email(data.email.lower())
        if user is None or not verify_password(data.password, user.password_hash):
            raise AuthError("Неверный email или пароль")
        if not user.is_active:
            raise AuthError("Аккаунт отключён")
        return user
