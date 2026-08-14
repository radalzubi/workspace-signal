from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from apps.api.core.config import Settings
from apps.api.db.models import Product
from apps.api.services.demo import bootstrap_demo
from apps.api.services.opportunities import (
    discount_band,
    expected_profit_model,
    opportunity_feed,
    price_band,
    saturation_penalty,
)


def test_expected_profit_calculation_uses_full_commercial_funnel() -> None:
    result = expected_profit_model(
        impressions=1000,
        ctr=Decimal("0.03"),
        conversion_rate=Decimal("0.05"),
        average_order_value=Decimal("80"),
        commission_rate=Decimal("0.06"),
        estimated_cost=Decimal("0.20"),
    )
    assert result["expected_clicks"] == Decimal("30.00")
    assert result["expected_conversions"] == Decimal("1.5000")
    assert result["expected_revenue"] == Decimal("7.20")
    assert result["expected_profit"] == Decimal("7.00")


def test_price_and_discount_bands_have_stable_boundaries() -> None:
    assert price_band(Decimal("24.99")) == "$0–25"
    assert price_band(Decimal("25")) == "$25–50"
    assert price_band(Decimal("250")) == "$250+"
    assert discount_band(Decimal("9.99")) == "0–10%"
    assert discount_band(Decimal("30")) == "30–40%"
    assert discount_band(Decimal("40")) == "40%+"


def test_demo_opportunity_feed_is_explainable_and_confidence_aware(db, tmp_path: Path) -> None:
    settings = Settings(media_root=tmp_path / "media", demo_mode=True, dry_run=True)
    bootstrap_demo(db, settings)
    feed = opportunity_feed(db)
    assert len(feed) == 6
    assert all(0 <= row["opportunity_score"] <= 100 for row in feed)
    assert all(
        row["expected_profit_low"] <= row["expected_profit_per_1000"] <= row["expected_profit_high"] for row in feed
    )
    assert all(row["rank_basis"] in {"expected_profit", "opportunity_score"} for row in feed)
    assert all(row["recommended_keyword_cluster"] and row["recommended_board"] for row in feed)
    assert all("primary_keyword" in row["score_breakdown"] for row in feed)
    assert len({row["expected_profit_per_1000"] for row in feed}) > 1


def test_repeated_product_receives_saturation_penalty(db, tmp_path: Path) -> None:
    settings = Settings(media_root=tmp_path / "media", demo_mode=True, dry_run=True)
    bootstrap_demo(db, settings)
    products = db.scalars(select(Product).order_by(Product.product_name)).all()
    promoted = next(item for item in products if item.product_name == "Compact Gas-Spring Monitor Arm")
    unpromoted = next(item for item in products if item.product_name == "Compact Ergonomic Vertical Mouse")
    assert saturation_penalty(db, promoted) > saturation_penalty(db, unpromoted)
