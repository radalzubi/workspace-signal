from datetime import UTC, datetime, timedelta
from decimal import Decimal

from apps.api.services.pricing import calculate_price_statistics


def test_price_history_uses_observed_low_language() -> None:
    now = datetime(2026, 8, 14, tzinfo=UTC)
    rows = [
        (now - timedelta(days=40), Decimal("100")),
        (now - timedelta(days=20), Decimal("90")),
        (now - timedelta(days=2), Decimal("80")),
        (now, Decimal("70")),
    ]
    result = calculate_price_statistics(rows, Decimal("70"), Decimal("100"), now)
    assert result["average_30d"] == Decimal("80.00")
    assert result["observed_all_time_low"] == Decimal("70")
    assert result["percent_below_30d_average"] == Decimal("12.50")
    assert result["claim_label"] == "Lowest price observed by our system"


def test_price_reference_discount_is_not_fabricated() -> None:
    now = datetime(2026, 8, 14, tzinfo=UTC)
    result = calculate_price_statistics([(now, Decimal("30"))], Decimal("30"), None, now)
    assert result["discount_from_reference_price"] == Decimal("0.00")
