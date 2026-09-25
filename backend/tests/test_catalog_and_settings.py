from fastapi.testclient import TestClient

from app.models import Service
from tests.conftest import create_manager, register_user


def test_services_requires_auth(api: TestClient):
    response = api.get("/api/services")
    assert response.status_code == 401


def test_services_list_returns_own_business_services(api: TestClient, db_session):
    headers, user = register_user(api, email="catalog@test.ru")
    db_session.add_all(
        [
            Service(business_id=user["business_id"], name="Стрижка", duration_minutes=60, price=1500),
            Service(business_id=user["business_id"], name="Маникюр", duration_minutes=90, price=1300),
        ]
    )
    db_session.commit()
    response = api.get("/api/services", headers=headers)
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"Стрижка", "Маникюр"}


def test_services_isolated_between_businesses(api: TestClient, db_session):
    _, user = register_user(api, email="catalog2@test.ru")
    other_headers, other_user = register_user(api, email="catalog3@test.ru", business="Другой салон")
    db_session.add(Service(business_id=other_user["business_id"], name="Чужая услуга"))
    db_session.commit()
    response = api.get("/api/services", headers=other_headers)
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert "Чужая услуга" in names


def test_settings_admin_ok(api: TestClient, admin_headers):
    response = api.get("/api/settings", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["ai_provider"] == "mock"
    assert body["ai_mode"] == "mock"
    assert body["ai_key_set"] is False
    assert body["telegram_bot_token_set"] is False


def test_settings_manager_forbidden(api: TestClient, db_session, admin_headers):
    _, user = register_user(api, email="settings@test.ru")
    manager = create_manager(db_session, user["business_id"])
    login = api.post("/api/auth/login", json={"email": manager.email, "password": "managerpass"})
    manager_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    response = api.get("/api/settings", headers=manager_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Доступ только для администратора"


def test_settings_requires_auth(api: TestClient):
    response = api.get("/api/settings")
    assert response.status_code == 401
