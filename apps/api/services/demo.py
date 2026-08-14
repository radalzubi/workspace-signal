from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import (
    AffiliateProgram,
    Click,
    Conversion,
    Cost,
    Experiment,
    ExperimentKeyword,
    Keyword,
    PerformanceEvent,
    Product,
    ProductPrice,
    ProductWatchlist,
)
from apps.api.services.affiliate import ensure_affiliate_link
from apps.api.services.affiliate_discovery import JSONAffiliateProgramProvider, discover_from_provider
from apps.api.services.analytics import keyword_performance_report, refresh_board_performance
from apps.api.services.content import generate_idea_and_variant
from apps.api.services.deals import detect_deals
from apps.api.services.ingestion import MockProductProvider, persist_observations
from apps.api.services.media import render_pin, render_video
from apps.api.services.opportunities import refresh_opportunities
from apps.api.services.optimization import create_daily_strategy, detect_winners
from apps.api.services.publishing import publish_variant
from apps.api.services.quality import validate_content
from apps.api.services.seo import seed_seo_taxonomy


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
    discover_from_provider(db, JSONAffiliateProgramProvider(settings.affiliate_directory_path))
    seed_seo_taxonomy(db, settings)
    publications = 0
    experiment = Experiment(
        name="Commercial keyword phrasing test",
        hypothesis=(
            "Specific space-saving language will produce more attributable profit than broad best-product language."
        ),
        allocation={"best_fit": 50, "space_saving": 50},
    )
    db.add(experiment)
    db.flush()
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
            db.add(Cost(kind="media", amount=Decimal("0.03"), content_id=variant.id, detail={"source": "demo"}))
    db.add_all(
        [
            Cost(kind="infrastructure", amount=Decimal("1.80"), detail={"source": "demo allocation"}),
            Cost(kind="ai", amount=Decimal("0.06"), detail={"source": "demo estimate"}),
        ]
    )
    db.commit()
    for label, term in [
        ("best_fit", "best monitor arm for small desk"),
        ("space_saving", "space saving monitor arm for small desk"),
    ]:
        keyword = db.scalar(select(Keyword).where(Keyword.normalized_keyword == term))
        if keyword:
            db.add(ExperimentKeyword(experiment_id=experiment.id, keyword_id=keyword.id, variant_label=label))
    if not db.scalar(select(ProductWatchlist).limit(1)):
        top_product = deals[0].product
        db.add_all(
            [
                ProductWatchlist(
                    name="Monitor leading desk opportunities",
                    product_id=top_product.id,
                    rule_type="opportunity_score_above",
                    threshold=Decimal("80"),
                ),
                ProductWatchlist(
                    name="Watch cable-management price deviation",
                    category="Cable Management",
                    rule_type="price_below_30d_percent",
                    threshold=Decimal("20"),
                ),
            ]
        )
    db.commit()
    detect_winners(db)
    keyword_performance_report(db, persist=True)
    refresh_board_performance(db)
    refresh_opportunities(db, settings)
    create_daily_strategy(db)
    return {
        "status": "initialized",
        "products": len(products),
        "deals": len(deals),
        "publications": publications,
        "affiliate_programs": int(db.scalar(select(func.count(AffiliateProgram.id))) or 0),
    }
