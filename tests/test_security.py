from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.session import get_db
from apps.api.main import app


def _client(db: Session) -> TestClient:
    def override_db():  # type: ignore[no-untyped-def]
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/overview",
        "/api/v1/products",
        "/api/v1/deals",
        "/api/v1/content",
        "/api/v1/publications",
        "/api/v1/costs",
        "/api/v1/experiments",
        "/api/v1/strategy",
        "/api/v1/reports/weekly",
        "/api/v1/seo/keywords",
        "/api/v1/opportunities",
        "/api/v1/affiliate-programs",
        "/api/v1/watchlists",
        "/api/v1/settings",
        "/api/v1/system-health",
    ],
)
def test_operational_reads_require_admin(db: Session, path: str) -> None:
    client = _client(db)
    response = client.get(path)
    assert response.status_code == 401
    app.dependency_overrides.clear()


def test_health_remains_public(db: Session) -> None:
    client = _client(db)
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    app.dependency_overrides.clear()


def test_admin_read_accepts_valid_bearer(db: Session) -> None:
    client = _client(db)
    response = client.get("/api/v1/products", headers={"Authorization": "Bearer test-admin-token"})
    assert response.status_code == 200
    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("admin_api_key", "demo-admin-change-me"),
        ("anonymization_salt", "demo-salt-change-me"),
        ("allowed_origins", "*"),
        ("allowed_hosts", "*"),
    ],
)
def test_production_rejects_insecure_configuration(field: str, value: str) -> None:
    secure = {
        "environment": "production",
        "admin_api_key": "a" * 32,
        "anonymization_salt": "b" * 32,
        "allowed_origins": "https://workspacesignal.com",
        "allowed_hosts": "workspacesignal.com",
    }
    secure[field] = value
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **secure)


def test_security_headers_are_applied(db: Session) -> None:
    client = _client(db)
    response = client.get("/api/v1/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"
    app.dependency_overrides.clear()
