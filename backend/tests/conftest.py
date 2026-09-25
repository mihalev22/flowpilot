import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "test-jwt-secret-with-enough-length"
os.environ["AI_MODE"] = "mock"
os.environ["AI_PROVIDER"] = "mock"
os.environ["TELEGRAM_WEBHOOK_SECRET"] = "test-telegram-secret"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import close_all_sessions, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings, get_settings
from app.core.rate_limit import reset_rate_limits
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import User
from app.models.enums import UserRole

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL", "sqlite://")

if TEST_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

test_settings = Settings(
    DATABASE_URL="sqlite://",
    JWT_SECRET="test-jwt-secret-with-enough-length",
    AI_MODE="mock",
    AI_PROVIDER="mock",
    TELEGRAM_WEBHOOK_SECRET="test-telegram-secret",
    CORS_ORIGINS="http://localhost:5173",
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_settings] = lambda: test_settings

client = TestClient(app)


def register_user(
    api: TestClient,
    email: str = "admin@test.ru",
    password: str = "secret123",
    business: str = "Тестовый салон",
) -> tuple[dict, dict]:
    response = api.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Тестовый Админ",
            "business_name": business,
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    return {"Authorization": f"Bearer {data['access_token']}"}, data["user"]


def create_manager(db, business_id: int, email: str = "manager@test.ru") -> User:
    user = User(
        business_id=business_id,
        email=email,
        password_hash=hash_password("managerpass"),
        full_name="Тестовый Менеджер",
        role=UserRole.MANAGER,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture(autouse=True)
def reset_db():
    close_all_sessions()
    reset_rate_limits()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    close_all_sessions()


@pytest.fixture()
def api() -> TestClient:
    return client


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def admin_headers(api: TestClient) -> dict:
    headers, _ = register_user(api)
    return headers
