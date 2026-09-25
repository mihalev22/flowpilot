import pytest
from fastapi.testclient import TestClient

from app.models import Client, Service
from tests.conftest import create_manager, register_user


@pytest.fixture()
def setup(api: TestClient, db_session):
    headers, user = register_user(api)
    client_row = Client(business_id=user["business_id"], name="Анна Тестова", phone="+7 900 111-22-33")
    service_row = Service(business_id=user["business_id"], name="Маникюр", duration_minutes=90, price=1300)
    db_session.add_all([client_row, service_row])
    db_session.commit()
    return headers, user, client_row, service_row


def test_create_request_web(api: TestClient, setup):
    headers, user, client_row, service_row = setup
    response = api.post(
        "/api/requests",
        headers=headers,
        json={"client_id": client_row.id, "text": "Хочу записаться на маникюр завтра в 15:00"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "NEW"
    assert body["source"] == "web"
    assert body["requires_manual_review"] is False
    assert body["service_id"] == service_row.id
    assert body["service_name"] == "Маникюр"
    assert body["preferred_date"] == "завтра"
    assert body["preferred_time"] == "15:00"
    assert body["created_by_user_id"] == user["id"]
    assert len(body["messages"]) == 1
    assert body["messages"][0]["source"] == "web"
    assert len(body["ai_analyses"]) == 1
    assert body["latest_ai"]["intent"] == "booking"
    assert body["latest_ai"]["confidence"] == 0.95


def test_create_request_low_confidence_manual_review(api: TestClient, setup):
    headers, _, client_row, _ = setup
    response = api.post(
        "/api/requests",
        headers=headers,
        json={"client_id": client_row.id, "text": "Добрый день!"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["requires_manual_review"] is True
    assert body["latest_ai"]["intent"] == "other"
    assert body["latest_ai"]["confidence"] < 0.60


def test_create_request_client_not_found(api: TestClient, setup):
    headers, _, _, _ = setup
    response = api.post(
        "/api/requests",
        headers=headers,
        json={"client_id": 9999, "text": "Привет"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Клиент не найден"


def test_list_and_get_request(api: TestClient, setup):
    headers, _, client_row, _ = setup
    create = api.post(
        "/api/requests",
        headers=headers,
        json={"client_id": client_row.id, "text": "Хочу записаться на стрижку завтра"},
    )
    request_id = create.json()["id"]
    listing = api.get("/api/requests", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    detail = api.get(f"/api/requests/{request_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == request_id


def test_get_request_not_found(api: TestClient, setup):
    headers, _, _, _ = setup
    response = api.get("/api/requests/12345", headers=headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Заявка не найдена"


def test_patch_status_creates_history(api: TestClient, setup):
    headers, _, client_row, _ = setup
    create = api.post(
        "/api/requests",
        headers=headers,
        json={"client_id": client_row.id, "text": "Сколько стоит массаж?"},
    )
    request_id = create.json()["id"]
    response = api.patch(f"/api/requests/{request_id}", headers=headers, json={"status": "IN_PROGRESS"})
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"
    detail = api.get(f"/api/requests/{request_id}", headers=headers).json()
    assert len(detail["status_history"]) == 1
    assert detail["status_history"][0]["old_status"] == "NEW"
    assert detail["status_history"][0]["new_status"] == "IN_PROGRESS"


def test_patch_same_status_no_history(api: TestClient, setup):
    headers, _, client_row, _ = setup
    create = api.post(
        "/api/requests",
        headers=headers,
        json={"client_id": client_row.id, "text": "Привет, вопрос про график"},
    )
    request_id = create.json()["id"]
    response = api.patch(f"/api/requests/{request_id}", headers=headers, json={"status": "NEW"})
    assert response.status_code == 200
    detail = api.get(f"/api/requests/{request_id}", headers=headers).json()
    assert len(detail["status_history"]) == 0


def test_patch_invalid_status(api: TestClient, setup):
    headers, _, client_row, _ = setup
    create = api.post(
        "/api/requests",
        headers=headers,
        json={"client_id": client_row.id, "text": "Вопрос про график"},
    )
    request_id = create.json()["id"]
    response = api.patch(f"/api/requests/{request_id}", headers=headers, json={"status": "BANANA"})
    assert response.status_code == 422


def test_patch_service_not_found(api: TestClient, setup):
    headers, _, client_row, _ = setup
    create = api.post(
        "/api/requests",
        headers=headers,
        json={"client_id": client_row.id, "text": "Вопрос"},
    )
    request_id = create.json()["id"]
    response = api.patch(f"/api/requests/{request_id}", headers=headers, json={"service_id": 999})
    assert response.status_code == 404
    assert response.json()["detail"] == "Услуга не найдена"


def test_requests_isolated_between_businesses(api: TestClient, setup):
    headers, _, client_row, _ = setup
    create = api.post(
        "/api/requests",
        headers=headers,
        json={"client_id": client_row.id, "text": "Хочу записаться на массаж завтра"},
    )
    request_id = create.json()["id"]
    headers2, _ = register_user(api, email="other@test.ru", business="Другой салон")
    listing = api.get("/api/requests", headers=headers2)
    assert listing.status_code == 200
    assert listing.json() == []
    detail = api.get(f"/api/requests/{request_id}", headers=headers2)
    assert detail.status_code == 404


def test_manager_can_manage_requests(api: TestClient, db_session, setup):
    headers, user, client_row, _ = setup
    manager = create_manager(db_session, user["business_id"])
    login = api.post("/api/auth/login", json={"email": manager.email, "password": "managerpass"})
    manager_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    create = api.post(
        "/api/requests",
        headers=manager_headers,
        json={"client_id": client_row.id, "text": "Хочу записаться на массаж завтра"},
    )
    assert create.status_code == 201
    patch = api.patch(
        f"/api/requests/{create.json()['id']}",
        headers=manager_headers,
        json={"status": "IN_PROGRESS"},
    )
    assert patch.status_code == 200


def test_dashboard_stats_admin_only(api: TestClient, db_session, setup):
    headers, user, client_row, _ = setup
    manager = create_manager(db_session, user["business_id"])
    login = api.post("/api/auth/login", json={"email": manager.email, "password": "managerpass"})
    manager_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = api.get("/api/dashboard/stats", headers=manager_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Доступ только для администратора"
    response = api.get("/api/dashboard/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 0
    assert body["status_counts"]["new"] == 0
    assert body["recent_requests"] == []


def test_dashboard_stats_counts(api: TestClient, setup):
    headers, _, client_row, _ = setup
    api.post("/api/requests", headers=headers, json={"client_id": client_row.id, "text": "Добрый день!"})
    create = api.post(
        "/api/requests",
        headers=headers,
        json={"client_id": client_row.id, "text": "Хочу записаться на стрижку завтра"},
    )
    api.patch(f"/api/requests/{create.json()['id']}", headers=headers, json={"status": "COMPLETED"})
    response = api.get("/api/dashboard/stats", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["status_counts"]["new"] == 1
    assert body["status_counts"]["completed"] == 1
    assert body["requires_review"] == 1
    assert body["by_source"] == [{"source": "web", "count": 2}]
    assert len(body["by_day"]) == 14
    assert sum(item["count"] for item in body["by_day"]) == 2
    assert len(body["recent_requests"]) == 2
