from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.db.models import Merchant, Product, ProductPrice
from apps.api.schemas import ProductObservation


class ProductProvider(ABC):
    """Replaceable source adapter. Implementations must return authorized assets only."""

    @abstractmethod
    def fetch(self) -> list[ProductObservation]:
        raise NotImplementedError


class MockProductProvider(ProductProvider):
    def __init__(self, niche: str = "small-space desk setup deals") -> None:
        self.niche = niche

    def fetch(self) -> list[ProductObservation]:
        now = datetime.now(UTC)
        rows = [
            (
                "compact-monitor-arm",
                "Compact Gas-Spring Monitor Arm",
                "Workspace Gear",
                "Monitor Arms",
                "Fits compact desks and supports VESA-compatible displays based on listed specifications.",
                "59.00",
                "89.00",
                "0.055",
            ),
            (
                "folding-laptop-stand",
                "Folding Aluminum Laptop Stand",
                "Northline",
                "Laptop Stands",
                "Adjustable folding stand designed to raise a laptop and free desk space.",
                "29.00",
                "49.00",
                "0.060",
            ),
            (
                "slim-power-strip",
                "Clamp-On Slim Desk Power Strip",
                "VoltDock",
                "Cable Management",
                "Clamp-mounted power strip with listed USB-C and AC outlets.",
                "39.00",
                "59.00",
                "0.050",
            ),
            (
                "under-desk-drawer",
                "Adhesive Under-Desk Storage Drawer",
                "TidyGrid",
                "Organization",
                "Low-profile drawer intended for stationery and small accessories.",
                "18.00",
                "27.00",
                "0.080",
            ),
            (
                "vertical-mouse",
                "Compact Ergonomic Vertical Mouse",
                "ArcInput",
                "Accessories",
                "Wireless vertical mouse sized for small work areas.",
                "34.00",
                "45.00",
                "0.045",
            ),
            (
                "desk-lamp",
                "Minimal LED Desk Lamp with USB-C",
                "LumaFold",
                "Lighting",
                "Foldable desk lamp with adjustable listed color-temperature modes.",
                "42.00",
                "70.00",
                "0.070",
            ),
        ]
        return [
            ProductObservation(
                provider="demo_catalog",
                provider_product_id=sku,
                product_name=name,
                brand=brand,
                category=category,
                description=description,
                current_price=Decimal(price),
                list_price=Decimal(list_price),
                currency="USD",
                canonical_product_url=f"https://example.com/products/{sku}",
                authorized_image_urls=[],
                authorized_video_urls=[],
                rating=None,
                review_count=None,
                availability="in_stock",
                merchant="Demo Merchant",
                merchant_domain="example.com",
                expected_commission_rate=Decimal(commission),
                observed_at=now,
            )
            for sku, name, brand, category, description, price, list_price, commission in rows
        ]


class CSVProductProvider(ProductProvider):
    def __init__(self, path: Path) -> None:
        self.path = path.resolve(strict=True)

    def fetch(self) -> list[ProductObservation]:
        if self.path.stat().st_size > 10_000_000:
            raise ValueError("CSV import exceeds 10 MB")
        with self.path.open(newline="", encoding="utf-8-sig") as handle:
            return [ProductObservation.model_validate(row) for row in csv.DictReader(handle)]


class JSONProductProvider(ProductProvider):
    def __init__(self, path: Path) -> None:
        self.path = path.resolve(strict=True)

    def fetch(self) -> list[ProductObservation]:
        if self.path.stat().st_size > 10_000_000:
            raise ValueError("JSON import exceeds 10 MB")
        data: Any = json.loads(self.path.read_text(encoding="utf-8"))
        return TypeAdapter(list[ProductObservation]).validate_python(data)


def persist_observations(db: Session, observations: list[ProductObservation]) -> list[Product]:
    products: list[Product] = []
    for item in observations:
        merchant = db.scalar(select(Merchant).where(Merchant.name == item.merchant))
        if merchant is None:
            merchant = Merchant(name=item.merchant, domain=item.merchant_domain)
            db.add(merchant)
            db.flush()
        product = db.scalar(
            select(Product).where(
                Product.provider == item.provider,
                Product.provider_product_id == item.provider_product_id,
            )
        )
        list_price = item.list_price
        discount = (
            ((list_price - item.current_price) / list_price * Decimal("100"))
            if list_price and list_price > item.current_price
            else Decimal("0")
        )
        values = {
            "product_name": item.product_name,
            "brand": item.brand,
            "category": item.category,
            "description": item.description,
            "current_price": item.current_price,
            "list_price": list_price,
            "currency": item.currency,
            "discount_percent": discount.quantize(Decimal("0.01")),
            "canonical_product_url": str(item.canonical_product_url),
            "authorized_image_urls": [str(url) for url in item.authorized_image_urls],
            "authorized_video_urls": [str(url) for url in item.authorized_video_urls],
            "rating": item.rating,
            "review_count": item.review_count,
            "availability": item.availability,
            "expected_commission_rate": item.expected_commission_rate,
            "merchant_id": merchant.id,
            "last_observed_at": item.observed_at,
        }
        if product is None:
            product = Product(
                provider=item.provider,
                provider_product_id=item.provider_product_id,
                **values,
            )
            db.add(product)
            db.flush()
        else:
            for key, value in values.items():
                setattr(product, key, value)
        duplicate = db.scalar(
            select(ProductPrice).where(
                ProductPrice.product_id == product.id,
                ProductPrice.observed_at == item.observed_at,
            )
        )
        if duplicate is None:
            db.add(
                ProductPrice(
                    product_id=product.id,
                    merchant_id=merchant.id,
                    price=item.current_price,
                    availability=item.availability,
                    observed_at=item.observed_at,
                )
            )
        products.append(product)
    db.commit()
    return products
