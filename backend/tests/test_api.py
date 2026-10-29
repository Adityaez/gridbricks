"""Tests for FastAPI HTTP endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify /api/health endpoint returns status ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_dashboard_date_validation():
    """Verify dates outside January 2026 are rejected with 400 Bad Request."""
    response = client.get("/api/dashboard?date=2026-02-01")
    assert response.status_code == 400
    assert "restricted" in response.json()["detail"].lower()

