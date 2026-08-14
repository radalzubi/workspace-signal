from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from apps.api.core.config import Settings


class PaidPromotionProvider:
    """Marker interface for official ad APIs or manual spend imports."""


@dataclass(frozen=True)
class PromotionSignal:
    winner_state: str
    impressions: int
    ctr: Decimal
    conversions: int
    requested_spend: Decimal
    daily_spend: Decimal
    monthly_spend: Decimal


def promotion_eligibility(signal: PromotionSignal, settings: Settings) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not settings.enable_paid_ads:
        failures.append("paid_ads_disabled")
    if min(settings.daily_ad_budget, settings.monthly_ad_budget, settings.max_spend_per_content) <= 0:
        failures.append("budgets_not_configured")
    if signal.winner_state != "winner":
        failures.append("content_not_winner")
    if signal.impressions < settings.min_organic_signal_before_promotion:
        failures.append("insufficient_organic_signal")
    if signal.ctr < settings.min_ctr:
        failures.append("ctr_below_threshold")
    if signal.conversions < settings.min_conversion_signal:
        failures.append("conversion_signal_below_threshold")
    if signal.requested_spend > settings.max_spend_per_content:
        failures.append("content_spend_limit")
    if signal.daily_spend + signal.requested_spend > settings.daily_ad_budget:
        failures.append("daily_budget_limit")
    if signal.monthly_spend + signal.requested_spend > settings.monthly_ad_budget:
        failures.append("monthly_budget_limit")
    return not failures, failures
