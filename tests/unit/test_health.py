"""Tests for the API health contract."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from docreader.main import app


def test_liveness_reports_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readiness_reports_ok_when_database_is_available() -> None:
    with (
        patch(
            "docreader.api.health.verify_database_connection",
            new_callable=AsyncMock,
        ) as verify,
        TestClient(app) as client,
    ):
        response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    verify.assert_awaited_once()


def test_readiness_reports_unavailable_when_database_fails() -> None:
    with (
        patch(
            "docreader.api.health.verify_database_connection",
            new_callable=AsyncMock,
            side_effect=SQLAlchemyError("connection failed"),
        ),
        TestClient(app) as client,
    ):
        response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database is unavailable"}
