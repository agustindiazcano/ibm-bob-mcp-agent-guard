"""Intentionally weak tests for the API — used as demo fixture for RepoGuard."""

from fastapi.testclient import TestClient
from shop.api import app

client = TestClient(app)


def test_health():
    # Only the health endpoint is tested — all other endpoints are uncovered
    response = client.get("/health")
    assert response.status_code == 200
