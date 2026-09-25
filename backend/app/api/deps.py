from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.models.enums import UserRole
from app.repositories.users import UserRepository
from app.services.ai import AIAnalysisService, build_provider
from app.services.analytics import AnalyticsService
from app.services.auth import AuthService
from app.services.catalog import CatalogService
from app.services.clients import ClientService
from app.services.requests import RequestService
from app.services.telegram import TelegramService

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None:
        raise AuthError("Требуется авторизация")
    user_id = decode_access_token(credentials.credentials, settings.JWT_SECRET)
    if user_id is None:
        raise AuthError("Недействительный или истёкший токен")
    user = UserRepository(db).get(user_id)
    if user is None or not user.is_active:
        raise AuthError("Пользователь не найден или отключён")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Доступ только для администратора")
    return user


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_ai_analysis_service(settings: Settings = Depends(get_settings)) -> AIAnalysisService:
    return AIAnalysisService(build_provider(settings))


def get_request_service(
    db: Session = Depends(get_db),
    ai_service: AIAnalysisService = Depends(get_ai_analysis_service),
) -> RequestService:
    return RequestService(db, ai_service)


def get_client_service(db: Session = Depends(get_db)) -> ClientService:
    return ClientService(db)


def get_catalog_service(db: Session = Depends(get_db)) -> CatalogService:
    return CatalogService(db)


def get_telegram_service(
    db: Session = Depends(get_db),
    request_service: RequestService = Depends(get_request_service),
    client_service: ClientService = Depends(get_client_service),
) -> TelegramService:
    return TelegramService(db, request_service, client_service)


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)
