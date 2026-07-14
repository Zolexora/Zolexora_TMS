import os

os.environ.setdefault("D1_GATEWAY_URL", "https://example.workers.dev")
os.environ.setdefault("D1_GATEWAY_TOKEN", "test-token")

from fastapi.testclient import TestClient
from app.main import app


def test_health_check():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_unauthenticated_request_returns_consistent_error_shape():
    with TestClient(app) as client:
        response = client.get("/api/companies")
        assert response.status_code == 401
        body = response.json()
        assert body["error"] == "Unauthorized"
        assert "requestId" in body


def test_malformed_bearer_token_does_not_crash():
    with TestClient(app) as client:
        response = client.get("/api/companies", headers={"Authorization": "Bearer not-a-jwt"})
        assert response.status_code == 401
