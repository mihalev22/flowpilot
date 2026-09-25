import base64
import json

from fastapi.testclient import TestClient

from app.core.rate_limit import RATE_LIMIT
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Client
from tests.conftest import register_user

WEBHOOK_SECRET = "test-telegram-secret"


def test_password_hashing_roundtrip():
    password_hash = hash_password("secret123")
    assert password_hash != "secret123"
    assert password_hash.startswith("$2")
    assert verify_password("secret123", password_hash)
    assert not verify_password("wrongpass", password_hash)


def test_password_not_exposed_in_responses(api: TestClient):
    headers, user = register_user(api, email="nohash@test.ru")
    assert "password_hash" not in user
    me = api.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert "password_hash" not in me.json()
    login = api.post(
        "/api/auth/login", json={"email": "nohash@test.ru", "password": "secret123"}
    )
    assert "password_hash" not in json.dumps(login.json())


def test_expired_token_rejected(api: TestClient):
    token = create_access_token(1, "test-jwt-secret-with-enough-length", -10)
    response = api.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_tampered_token_rejected(api: TestClient):
    _, user = register_user(api, email="tamper@test.ru")
    token = create_access_token(user["id"], "test-jwt-secret-with-enough-length", 60)
    header_b64, payload_b64, signature = token.split(".")
    payload = json.loads(base64.urlsafe_b64decode(payload_b64 + "==="))
    payload["sub"] = "999"
    new_payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    tampered = f"{header_b64}.{new_payload_b64}.{signature}"
    response = api.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered}"})
    assert response.status_code == 401


def test_structurally_broken_token_rejected(api: TestClient):
    response = api.get("/api/auth/me", headers={"Authorization": "Bearer abc.def.ghi"})
    assert response.status_code == 401


def test_webhook_wrong_secret_value_rejected(api: TestClient):
    payload = {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "from": {"id": 1, "first_name": "Тест"},
            "text": "Привет",
        },
    }
    response = api.post(
        "/api/webhooks/telegram", json=payload, headers={"X-Telegram-Secret": "totally-wrong"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Недействительный секрет вебхука"
    assert "test-telegram-secret" not in response.text


def test_login_rate_limited(api: TestClient):
    credentials = {"email": "nobody@test.ru", "password": "wrongpass1"}
    for _ in range(RATE_LIMIT):
        response = api.post("/api/auth/login", json=credentials)
        assert response.status_code == 401
    response = api.post("/api/auth/login", json=credentials)
    assert response.status_code == 429
    assert response.json()["detail"] == "Слишком много запросов. Попробуйте позже."
    assert "retry-after" in response.headers


def test_register_rate_limited(api: TestClient):
    invalid = {"email": "bad", "password": "1", "full_name": "", "business_name": ""}
    for _ in range(RATE_LIMIT):
        response = api.post("/api/auth/register", json=invalid)
        assert response.status_code == 422
    response = api.post("/api/auth/register", json=invalid)
    assert response.status_code == 429


def test_webhook_rate_limited(api: TestClient, admin_headers):
    payload = {"update_id": 1, "message": None}
    for _ in range(RATE_LIMIT):
        response = api.post(
            "/api/webhooks/telegram", json=payload, headers={"X-Telegram-Secret": "wrong"}
        )
        assert response.status_code == 403
    response = api.post(
        "/api/webhooks/telegram", json=payload, headers={"X-Telegram-Secret": "wrong"}
    )
    assert response.status_code == 429


def test_rate_limit_scoped_to_limited_paths(api: TestClient, admin_headers):
    credentials = {"email": "nobody2@test.ru", "password": "wrongpass1"}
    for _ in range(RATE_LIMIT):
        api.post("/api/auth/login", json=credentials)
    health = api.get("/api/health")
    assert health.status_code == 200
    requests_list = api.get("/api/requests", headers=admin_headers)
    assert requests_list.status_code == 200


def test_create_request_text_too_long(api: TestClient, db_session, admin_headers):
    _, user = register_user(api, email="oversize@test.ru")
    client_row = Client(business_id=user["business_id"], name="Тестовый Клиент")
    db_session.add(client_row)
    db_session.commit()
    response = api.post(
        "/api/requests",
        headers=admin_headers,
        json={"client_id": client_row.id, "text": "а" * 4001},
    )
    assert response.status_code == 422


def test_create_request_empty_text(api: TestClient, db_session, admin_headers):
    _, user = register_user(api, email="emptytext@test.ru")
    client_row = Client(business_id=user["business_id"], name="Тестовый Клиент")
    db_session.add(client_row)
    db_session.commit()
    response = api.post(
        "/api/requests", headers=admin_headers, json={"client_id": client_row.id, "text": ""}
    )
    assert response.status_code == 422


def test_requests_pagination_bounds(api: TestClient, admin_headers):
    big_limit = api.get("/api/requests?limit=99999", headers=admin_headers)
    assert big_limit.status_code == 422
    negative_offset = api.get("/api/requests?offset=-1", headers=admin_headers)
    assert negative_offset.status_code == 422


def test_clients_search_too_long(api: TestClient, admin_headers):
    response = api.get("/api/clients", params={"search": "а" * 300}, headers=admin_headers)
    assert response.status_code == 422


def test_telegram_long_name_trimmed(api: TestClient, admin_headers):
    payload = {
        "update_id": 501,
        "message": {
            "message_id": 1,
            "from": {"id": 900001, "first_name": "А" * 300, "last_name": ""},
            "text": "Хочу записаться на стрижку",
        },
    }
    response = api.post(
        "/api/webhooks/telegram", json=payload, headers={"X-Telegram-Secret": WEBHOOK_SECRET}
    )
    assert response.status_code == 200
    clients = api.get("/api/clients", headers=admin_headers).json()
    assert len(clients) == 1
    assert len(clients[0]["name"]) <= 200


def test_internal_error_returns_generic_message():
    from fastapi.testclient import TestClient as Client

    from app.main import app

    def boom():
        raise RuntimeError("secret value C:\\private\\path token=abc123")

    app.add_api_route("/api/_boom", boom, methods=["GET"], include_in_schema=False)
    try:
        response = Client(app, raise_server_exceptions=False).get("/api/_boom")
        assert response.status_code == 500
        assert response.json()["detail"] == "Внутренняя ошибка сервера"
        assert "secret value" not in response.text
        assert "RuntimeError" not in response.text
        assert "Traceback" not in response.text
    finally:
        app.router.routes = [
            route for route in app.router.routes if getattr(route, "path", None) != "/api/_boom"
        ]
