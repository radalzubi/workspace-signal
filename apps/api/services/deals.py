from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import Deal, Product
from apps.api.services.pricing import product_price_statistics
from apps.api.services.scoring import score_deal


def detect_deals(db: Session, settings: Settings) -> list[Deal]:
    products = db.scalars(
        select(Product).where(
            Product.availability == "in_stock",
            Product.current_price >= settings.min_price,
            Product.current_price <= settings.max_price,
        )
    ).all()
    deals: list[Deal] = []
    for product in products:
        stats = product_price_statistics(db, product)
        if (
            stats["discount_from_reference_price"] < settings.min_discount_percent
            and stats["percent_below_30d_average"] < settings.min_discount_percent
        ):
            continue
        result = score_deal(product, stats, merchant_quality=Decimal(product.merchant.quality_score))
        deal = db.scalar(select(Deal).where(Deal.product_id == product.id, Deal.status == "active"))
        payload = {
            "deal_score": result.score,
            "expected_profit_per_1000": result.expected_profit_per_1000,
            "score_factors": result.factors,
            "price_statistics": {
                key: float(value) if isinstance(value, Decimal) else value for key, value in stats.items()
            },
            "expires_at": datetime.now(UTC) + timedelta(hours=settings.deal_max_age_hours),
        }
        if deal is None:
            deal = Deal(product_id=product.id, status="active", **payload)
            db.add(deal)
        else:
            for key, value in payload.items():
                setattr(deal, key, value)
        deals.append(deal)
    db.commit()
    return deals
