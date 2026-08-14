from decimal import Decimal

from apps.api.core.config import Settings
from apps.api.services.promotion import PromotionSignal, promotion_eligibility


def signal(**changes) -> PromotionSignal:
    values = {
        "winner_state": "winner",
        "impressions": 1000,
        "ctr": Decimal("0.03"),
        "conversions": 2,
        "requested_spend": Decimal("10"),
        "daily_spend": Decimal("0"),
        "monthly_spend": Decimal("0"),
    }
    values.update(changes)
    return PromotionSignal(**values)


def enabled_settings() -> Settings:
    return Settings(
        enable_paid_ads=True,
        daily_ad_budget=Decimal("20"),
        monthly_ad_budget=Decimal("200"),
        max_spend_per_content=Decimal("15"),
    )


def test_paid_promotion_defaults_off() -> None:
    eligible, failures = promotion_eligibility(signal(), Settings())
    assert not eligible
    assert "paid_ads_disabled" in failures
    assert "budgets_not_configured" in failures


def test_all_budget_and_signal_gates_must_pass() -> None:
    assert promotion_eligibility(signal(), enabled_settings()) == (True, [])
    eligible, failures = promotion_eligibility(signal(requested_spend=Decimal("16")), enabled_settings())
    assert not eligible
    assert "content_spend_limit" in failures
