from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from apps.api.db.models import Product
from apps.api.services.pricing import PriceStatistics

DEFAULT_WEIGHTS = {
    "discount": Decimal("0.24"),
    "price_history": Decimal("0.20"),
    "commission": Decimal("0.18"),
    "merchant": Decimal("0.10"),
    "audience_relevance": Decimal("0.16"),
    "novelty": Decimal("0.07"),
    "availability": Decimal("0.05"),
}


@dataclass(frozen=True)
class DealScore:
    score: Decimal
    expected_profit_per_1000: Decimal
    factors: dict[str, float | str]


def score_deal(
    product: Product,
    stats: PriceStatistics,
    *,
    merchant_quality: Decimal = Decimal("75"),
    audience_relevance: Decimal = Decimal("82"),
    novelty: Decimal = Decimal("70"),
    predicted_ctr: Decimal = Decimal("0.018"),
    predicted_conversion_rate: Decimal = Decimal("0.035"),
    estimated_promotion_cost: Decimal = Decimal("0"),
    weights: dict[str, Decimal] | None = None,
) -> DealScore:
    weights = weights or DEFAULT_WEIGHTS
    discount_component = min(stats["discount_from_reference_price"] * Decimal("2.5"), Decimal("100"))
    history_component = min(
        max(stats["percent_below_30d_average"] * Decimal("4"), Decimal("0")),
        Decimal("100"),
    )
    commission_value = Decimal(product.current_price) * Decimal(product.expected_commission_rate)
    commission_component = min(commission_value / Decimal("8") * Decimal("100"), Decimal("100"))
    availability = Decimal("100") if product.availability == "in_stock" else Decimal("0")
    components = {
        "discount": discount_component,
        "price_history": history_component,
        "commission": commission_component,
        "merchant": merchant_quality,
        "audience_relevance": audience_relevance,
        "novelty": novelty,
        "availability": availability,
    }
    score = sum((components[key] * weights[key] for key in weights), start=Decimal("0")).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
    predicted_clicks = Decimal("1000") * predicted_ctr
    commission = Decimal(product.current_price) * Decimal(product.expected_commission_rate)
    expected_profit = (predicted_clicks * predicted_conversion_rate * commission - estimated_promotion_cost).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
    factors: dict[str, float | str] = {key: float(value.quantize(Decimal("0.01"))) for key, value in components.items()}
    factors.update(
        {
            "summary": (
                f"{stats['claim_label']}; score emphasizes verified discount, observed history, "
                "audience fit, and expected commission."
            ),
            "predicted_ctr": float(predicted_ctr),
            "predicted_conversion_rate": float(predicted_conversion_rate),
        }
    )
    return DealScore(score=min(score, Decimal("100")), expected_profit_per_1000=expected_profit, factors=factors)
