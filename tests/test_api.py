"""API tests for the dashboard backend."""

from __future__ import annotations

from fastapi.testclient import TestClient

from optimize.api.app import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_experiments() -> None:
    response = client.get("/api/experiments")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard() -> None:
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert "experiments" in payload
    assert "studies" in payload
