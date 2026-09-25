from fastapi import APIRouter, Depends

from app.api.deps import get_auth_service, get_current_user
from app.core.config import Settings, get_settings
from app.core.security import create_access_token
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn, TokenOut, UserOut
from app.services.auth import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _token_response(user: User, settings: Settings) -> TokenOut:
    token = create_access_token(user.id, settings.JWT_SECRET, settings.JWT_EXPIRE_MINUTES)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/register", response_model=TokenOut, status_code=201)
def register(
    data: RegisterIn,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> TokenOut:
    user = service.register(data)
    return _token_response(user, settings)


@router.post("/login", response_model=TokenOut)
def login(
    data: LoginIn,
    service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> TokenOut:
    user = service.login(data)
    return _token_response(user, settings)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
