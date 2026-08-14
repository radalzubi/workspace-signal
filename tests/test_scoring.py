from decimal import Decimal

from apps.api.db.models import Product
from apps.api.services.pricing import PriceStatistics
from apps.api.services.scoring import score_deal


def product() -> Product:
    return Product(
        provider="test",
        provider_product_id="1",
        product_name="Monitor arm",
        category="Desk",
        description="Listed VESA support",
        current_price=Decimal("50"),
        list_price=Decimal("100"),
        currency="USD",
        discount_percent=Decimal("50"),
        canonical_product_url="https://example.com/1",
        availability="in_stock",
        expected_commission_rate=Decimal("0.08"),
        merchant_id="merchant",
    )


def stats() -> PriceStatistics:
    return PriceStatistics(
        current_price=Decimal("50"),
        average_7d=Decimal("70"),
        average_30d=Decimal("75"),
        average_90d=Decimal("80"),
        observed_all_time_low=Decimal("50"),
        percent_below_30d_average=Decimal("33.33"),
        discount_from_reference_price=Decimal("50"),
        observation_count=30,
        claim_label="Lowest price observed by our system",
    )


def test_score_is_bounded_and_explainable() -> None:
    result = score_deal(product(), stats())
    assert Decimal("0") <= result.score <= Decimal("100")
    assert result.expected_profit_per_1000 > 0
    assert result.factors["availability"] == 100.0
    assert "observed" in str(result.factors["summary"]).lower()


def test_out_of_stock_product_loses_availability_points() -> None:
    item = product()
    item.availability = "out_of_stock"
    assert score_deal(item, stats()).factors["availability"] == 0.0
