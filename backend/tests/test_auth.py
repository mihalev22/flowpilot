from fastapi.testclient import TestClient

from tests.conftest import register_user


def test_register_success(api: TestClient):
    headers, user = register_user(api, email="new@test.ru")
    assert user["role"] == "admin"
    assert user["business_id"] == 1
    response = api.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "new@test.ru"


def test_register_duplicate_email(api: TestClient):
    register_user(api, email="dup@test.ru")
    response = api.post(
        "/api/auth/register",
        json={
            "email": "dup@test.ru",
            "password": "secret123",
            "full_name": "Второй Админ",
            "business_name": "Второй салон",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Пользователь с таким email уже зарегистрирован"


def test_register_short_password(api: TestClient):
    response = api.post(
        "/api/auth/register",
        json={
            "email": "short@test.ru",
            "password": "123",
            "full_name": "Короткий Пароль",
            "business_name": "Салон",
        },
    )
    assert response.status_code == 422


def test_login_success(api: TestClient):
    register_user(api, email="login@test.ru", password="secret123")
    response = api.post("/api/auth/login", json={"email": "login@test.ru", "password": "secret123"})
    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["user"]["email"] == "login@test.ru"


def test_login_wrong_password(api: TestClient):
    register_user(api, email="login2@test.ru", password="secret123")
    response = api.post("/api/auth/login", json={"email": "login2@test.ru", "password": "wrongpass"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Неверный email или пароль"


def test_login_unknown_email(api: TestClient):
    response = api.post("/api/auth/login", json={"email": "ghost@test.ru", "password": "whatever1"})
    assert response.status_code == 401


def test_me_without_token(api: TestClient):
    response = api.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Требуется авторизация"


def test_me_invalid_token(api: TestClient):
    response = api.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == 401
