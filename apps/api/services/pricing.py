from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.db.models import Product, ProductPrice


class PriceStatistics(TypedDict):
    current_price: Decimal
    average_7d: Decimal | None
    average_30d: Decimal | None
    average_90d: Decimal | None
    observed_all_time_low: Decimal
    percent_below_30d_average: Decimal
    discount_from_reference_price: Decimal
    observation_count: int
    claim_label: str


def _average(values: list[Decimal]) -> Decimal | None:
    if not values:
        return None
    return (sum(values, Decimal("0")) / len(values)).quantize(Decimal("0.01"), ROUND_HALF_UP)


def calculate_price_statistics(
    observations: list[tuple[datetime, Decimal]],
    current_price: Decimal,
    list_price: Decimal | None,
    now: datetime | None = None,
) -> PriceStatistics:
    if not observations:
        observations = [((now or datetime.now(UTC)), current_price)]
    now = now or max(timestamp for timestamp, _ in observations)

    def window(days: int) -> list[Decimal]:
        cutoff = now - timedelta(days=days)
        return [price for timestamp, price in observations if timestamp >= cutoff]

    avg_7 = _average(window(7))
    avg_30 = _average(window(30))
    avg_90 = _average(window(90))
    below_avg = ((avg_30 - current_price) / avg_30 * 100) if avg_30 and avg_30 else Decimal("0")
    reference_discount = (
        ((list_price - current_price) / list_price * 100) if list_price and list_price > current_price else Decimal("0")
    )
    return PriceStatistics(
        current_price=current_price,
        average_7d=avg_7,
        average_30d=avg_30,
        average_90d=avg_90,
        observed_all_time_low=min(price for _, price in observations),
        percent_below_30d_average=below_avg.quantize(Decimal("0.01"), ROUND_HALF_UP),
        discount_from_reference_price=reference_discount.quantize(Decimal("0.01"), ROUND_HALF_UP),
        observation_count=len(observations),
        claim_label="Lowest price observed by our system"
        if current_price == min(p for _, p in observations)
        else "Current listed price",
    )


def product_price_statistics(db: Session, product: Product) -> PriceStatistics:
    rows = db.execute(
        select(ProductPrice.observed_at, ProductPrice.price)
        .where(ProductPrice.product_id == product.id)
        .order_by(ProductPrice.observed_at)
    ).all()
    return calculate_price_statistics(
        [(row.observed_at, Decimal(row.price)) for row in rows],
        Decimal(product.current_price),
        Decimal(product.list_price) if product.list_price is not None else None,
    )
