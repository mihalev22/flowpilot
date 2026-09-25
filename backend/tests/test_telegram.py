from fastapi.testclient import TestClient

WEBHOOK_SECRET = "test-telegram-secret"


def webhook_payload(
    update_id: int = 1,
    text: str = "Хочу записаться на массаж завтра в 15:00",
    tg_user_id: int = 200001,
) -> dict:
    return {
        "update_id": update_id,
        "message": {
            "message_id": 10,
            "from": {"id": tg_user_id, "first_name": "Ольга", "last_name": "Тестова", "username": "olga_t"},
            "text": text,
        },
    }


def webhook_headers() -> dict:
    return {"X-Telegram-Secret": WEBHOOK_SECRET}


def test_webhook_wrong_secret(api: TestClient, admin_headers):
    response = api.post("/api/webhooks/telegram", json=webhook_payload())
    assert response.status_code == 403
    assert response.json()["detail"] == "Недействительный секрет вебхука"


def test_webhook_without_business(api: TestClient):
    response = api.post("/api/webhooks/telegram", json=webhook_payload(), headers=webhook_headers())
    assert response.status_code == 404
    assert "Бизнес не найден" in response.json()["detail"]


def test_webhook_creates_request_and_client(api: TestClient, admin_headers):
    response = api.post("/api/webhooks/telegram", json=webhook_payload(), headers=webhook_headers())
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["request_id"] is not None
    assert body["detail"] == "Обновление обработано"

    requests = api.get("/api/requests", headers=admin_headers).json()
    assert len(requests) == 1
    request = requests[0]
    assert request["source"] == "telegram"
    assert request["status"] == "NEW"
    assert request["requires_manual_review"] is False
    assert request["latest_ai"]["intent"] == "booking"
    assert request["latest_ai"]["service_name"] == "Массаж"

    clients = api.get("/api/clients", headers=admin_headers).json()
    assert len(clients) == 1
    assert clients[0]["name"] == "Ольга Тестова"
    assert clients[0]["telegram_user_id"] == 200001

    detail = api.get(f"/api/requests/{body['request_id']}", headers=admin_headers).json()
    assert detail["messages"][0]["telegram_update_id"] == 1
    assert detail["messages"][0]["source"] == "telegram"


def test_webhook_duplicate_update_no_new_request(api: TestClient, admin_headers):
    payload = webhook_payload(update_id=42)
    first = api.post("/api/webhooks/telegram", json=payload, headers=webhook_headers())
    assert first.status_code == 200
    assert first.json()["request_id"] is not None
    second = api.post("/api/webhooks/telegram", json=payload, headers=webhook_headers())
    assert second.status_code == 200
    assert second.json()["request_id"] is None
    requests = api.get("/api/requests", headers=admin_headers).json()
    assert len(requests) == 1


def test_webhook_same_client_second_update(api: TestClient, admin_headers):
    first = api.post(
        "/api/webhooks/telegram", json=webhook_payload(update_id=1), headers=webhook_headers()
    )
    assert first.json()["request_id"] is not None
    second = api.post(
        "/api/webhooks/telegram", json=webhook_payload(update_id=2, text="Сколько стоит маникюр?"),
        headers=webhook_headers(),
    )
    assert second.json()["request_id"] is not None
    clients = api.get("/api/clients", headers=admin_headers).json()
    assert len(clients) == 1
    requests = api.get("/api/requests", headers=admin_headers).json()
    assert len(requests) == 2


def test_webhook_update_without_message(api: TestClient, admin_headers):
    response = api.post(
        "/api/webhooks/telegram", json={"update_id": 777}, headers=webhook_headers()
    )
    assert response.status_code == 200
    assert response.json()["request_id"] is None
    assert api.get("/api/requests", headers=admin_headers).json() == []


def test_webhook_invalid_payload(api: TestClient):
    response = api.post("/api/webhooks/telegram", json={"foo": "bar"}, headers=webhook_headers())
    assert response.status_code == 422
