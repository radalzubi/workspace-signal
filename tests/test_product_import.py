from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.db.models import Product
from apps.api.db.session import get_db
from apps.api.main import app


def test_product_import_is_admin_only_and_upserts(db: Session) -> None:
    def override_db():  # type: ignore[no-untyped-def]
        yield db

    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    payload = [
        {
            "provider": "official_merchant_research",
            "provider_product_id": "anker-a91c0",
            "product_name": "Anker 525 Charging Station",
            "brand": "Anker",
            "category": "Charging",
            "description": "Three AC outlets, two USB-C ports and two USB-A ports.",
            "current_price": "39.99",
            "currency": "USD",
            "canonical_product_url": "https://www.anker.com/products/a91c0",
            "availability": "in_stock",
            "merchant": "Anker",
            "merchant_domain": "anker.com",
            "expected_commission_rate": "0.08",
            "observed_at": "2026-08-16T00:00:00Z",
        }
    ]

    assert client.post("/api/v1/products/import", json=payload).status_code == 401
    headers = {"Authorization": "Bearer test-admin-token"}
    response = client.post("/api/v1/products/import", json=payload, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"imported": 1}

    payload[0]["current_price"] = "37.99"
    response = client.post("/api/v1/products/import", json=payload, headers=headers)
    assert response.status_code == 200
    products = list(db.scalars(select(Product)).all())
    assert len(products) == 1
    assert float(products[0].current_price) == 37.99
    app.dependency_overrides.clear()
