from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import (
    Click,
    Conversion,
    Cost,
    Experiment,
    PerformanceEvent,
    Product,
    ProductPrice,
)
from apps.api.services.affiliate import ensure_affiliate_link
from apps.api.services.content import generate_idea_and_variant
from apps.api.services.deals import detect_deals
from apps.api.services.ingestion import MockProductProvider, persist_observations
from apps.api.services.media import render_pin, render_video
from apps.api.services.optimization import create_daily_strategy, detect_winners
from apps.api.services.publishing import publish_variant
from apps.api.services.quality import validate_content


def bootstrap_demo(db: Session, settings: Settings) -> dict[str, int | str]:
    existing = int(db.scalar(select(func.count(Product.id))) or 0)
    if existing:
        return {"status": "already_initialized", "products": existing}
    products = persist_observations(db, MockProductProvider(settings.niche).fetch())
    now = datetime.now(UTC)
    for product_index, product in enumerate(products):
        current = Decimal(product.current_price)
        for days_ago in range(1, 91, 3):
            premium = Decimal("1.18") + Decimal((days_ago + product_index) % 9) / Decimal("100")
            db.add(
                ProductPrice(
                    product_id=product.id,
                    merchant_id=product.merchant_id,
                    price=(current * premium).quantize(Decimal("0.01")),
                    availability="in_stock",
                    observed_at=now - timedelta(days=days_ago),
                )
            )
    db.commit()
    deals = sorted(detect_deals(db, settings), key=lambda item: item.deal_score, reverse=True)
    publications = 0
    for index, deal in enumerate(deals[:4]):
        variant = generate_idea_and_variant(
            db, deal, settings, ["deal_alert", "under_50", "price_drop", "small_space"][index]
        )
        ensure_affiliate_link(db, variant, settings, affiliate_id="demo-partner")
        render_pin(db, variant, settings)
        if index == 0:
            render_video(db, variant, settings)
        report = validate_content(db, variant, settings)
        if report["passed"]:
            variant.status = "approved"
            db.commit()
            link = ensure_affiliate_link(db, variant, settings, affiliate_id="demo-partner")
            publication = publish_variant(db, variant, link, settings)
            publications += 1
            impressions = [1600, 980, 620, 410][index]
            clicks = [58, 24, 11, 4][index]
            db.add(
                PerformanceEvent(
                    publication_id=publication.id,
                    event_type="impression",
                    count=impressions,
                    occurred_at=now - timedelta(days=index),
                )
            )
            for click_index in range(clicks):
                db.add(
                    Click(
                        affiliate_link_id=link.id,
                        content_id=variant.id,
                        platform="pinterest",
                        campaign=link.campaign,
                        referrer="https://www.pinterest.com/",
                        visitor_hash=f"demo-{index}-{click_index}",
                        clicked_at=now - timedelta(days=index),
                    )
                )
            if index < 3:
                db.add(
                    Conversion(
                        provider="demo_affiliate",
                        external_id=f"demo-order-{index}",
                        product_id=deal.product_id,
                        content_id=variant.id,
                        campaign=link.campaign,
                        order_value=Decimal([89, 58, 39][index]),
                        commission=Decimal([5.34, 3.48, 3.12][index]),
                        currency="USD",
                        converted_at=now - timedelta(days=index),
                    )
                )
    db.add_all(
        [
            Cost(kind="infrastructure", amount=Decimal("1.80"), detail={"source": "demo allocation"}),
            Cost(kind="ai", amount=Decimal("0.06"), detail={"source": "demo estimate"}),
            Experiment(
                name="Value hook vs. space-saving hook",
                hypothesis="Space-saving language will improve outbound CTR for compact-desk products.",
                allocation={"value": 50, "space_saving": 50},
            ),
        ]
    )
    db.commit()
    detect_winners(db)
    create_daily_strategy(db)
    return {
        "status": "initialized",
        "products": len(products),
        "deals": len(deals),
        "publications": publications,
    }
