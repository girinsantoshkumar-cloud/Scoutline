from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_health_and_readiness_are_available():
    health = client.get("/api/health")
    ready = client.get("/api/ready")
    assert health.status_code == 200
    assert health.json()["ok"] is True
    assert ready.status_code == 200
    assert ready.json()["ready"] is True


def test_metrics_endpoint_exposes_prometheus_format():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "scoutline_http_requests_total" in response.text or "python_info" in response.text


def test_authenticated_routes_reject_missing_token():
    response = client.get("/api/dashboard")
    assert response.status_code == 401


def test_register_me_and_logout_flow():
    payload = {
        "name": "Test User",
        "email": "ci-user@example.invalid",
        "password": "not-a-real-password",
    }
    registered = client.post("/api/auth/register", json=payload)
    assert registered.status_code == 201
    token = registered.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == payload["email"]

    logged_out = client.post("/api/auth/logout", headers=headers)
    assert logged_out.status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_duplicate_registration_is_rejected():
    payload = {
        "name": "Duplicate User",
        "email": "duplicate-ci@example.invalid",
        "password": "not-a-real-password",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    assert client.post("/api/auth/register", json=payload).status_code == 409
