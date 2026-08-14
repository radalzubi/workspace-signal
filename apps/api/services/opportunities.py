from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import (
    AffiliateProgram,
    AffiliateProgramScore,
    Click,
    ContentIdea,
    ContentVariant,
    Conversion,
    Cost,
    Deal,
    Keyword,
    KeywordCluster,
    KeywordClusterMember,
    PerformanceEvent,
    PinterestBoard,
    Product,
    ProductKeyword,
    ProductOpportunity,
    ProductProblem,
    ProductWatchlist,
    Publication,
)
from apps.api.services.affiliate_discovery import score_affiliate_program
from apps.api.services.seo import load_seo_taxonomy, seed_seo_taxonomy, select_board


def price_band(price: Decimal) -> str:
    if price < 25:
        return "$0–25"
    if price < 50:
        return "$25–50"
    if price < 100:
        return "$50–100"
    if price < 250:
        return "$100–250"
    return "$250+"


def discount_band(discount: Decimal) -> str:
    if discount < 10:
        return "0–10%"
    if discount < 20:
        return "10–20%"
    if discount < 30:
        return "20–30%"
    if discount < 40:
        return "30–40%"
    return "40%+"


def expected_profit_model(
    *,
    impressions: int,
    ctr: Decimal,
    conversion_rate: Decimal,
    average_order_value: Decimal,
    commission_rate: Decimal,
    estimated_cost: Decimal,
) -> dict[str, Decimal]:
    expected_clicks = Decimal(impressions) * ctr
    expected_conversions = expected_clicks * conversion_rate
    expected_revenue = expected_conversions * average_order_value * commission_rate
    return {
        "expected_clicks": expected_clicks.quantize(Decimal("0.01")),
        "expected_conversions": expected_conversions.quantize(Decimal("0.0001")),
        "expected_revenue": expected_revenue.quantize(Decimal("0.01"), ROUND_HALF_UP),
        "expected_profit": (expected_revenue - estimated_cost).quantize(Decimal("0.01"), ROUND_HALF_UP),
    }


def saturation_penalty(db: Session, product: Product, *, now: datetime | None = None) -> Decimal:
    since = (now or datetime.now(UTC)) - timedelta(days=30)
    product_posts = int(
        db.scalar(
            select(func.count(ContentVariant.id))
            .join(ContentIdea, ContentIdea.id == ContentVariant.idea_id)
            .join(Deal, Deal.id == ContentIdea.deal_id)
            .where(Deal.product_id == product.id, ContentVariant.created_at >= since)
        )
        or 0
    )
    category_posts = int(
        db.scalar(
            select(func.count(ContentVariant.id))
            .join(ContentIdea, ContentIdea.id == ContentVariant.idea_id)
            .join(Deal, Deal.id == ContentIdea.deal_id)
            .join(Product, Product.id == Deal.product_id)
            .where(Product.category == product.category, ContentVariant.created_at >= since)
        )
        or 0
    )
    return min(Decimal("100"), Decimal(product_posts * 18 + max(category_posts - 4, 0) * 4))


def _historical_product_metrics(db: Session, product: Product) -> dict[str, Decimal | int]:
    content_ids = list(
        db.scalars(
            select(ContentVariant.id)
            .join(ContentIdea, ContentIdea.id == ContentVariant.idea_id)
            .join(Deal, Deal.id == ContentIdea.deal_id)
            .where(Deal.product_id == product.id)
        ).all()
    )
    if not content_ids:
        return {"impressions": 0, "clicks": 0, "conversions": 0, "revenue": Decimal("0"), "cost": Decimal("0")}
    publication_ids = list(db.scalars(select(Publication.id).where(Publication.content_id.in_(content_ids))).all())
    impressions = int(
        db.scalar(
            select(func.coalesce(func.sum(PerformanceEvent.count), 0)).where(
                PerformanceEvent.publication_id.in_(publication_ids),
                PerformanceEvent.event_type == "impression",
            )
        )
        or 0
    )
    clicks = int(db.scalar(select(func.count(Click.id)).where(Click.content_id.in_(content_ids))) or 0)
    conversions = int(db.scalar(select(func.count(Conversion.id)).where(Conversion.content_id.in_(content_ids))) or 0)
    revenue = Decimal(
        db.scalar(
            select(func.coalesce(func.sum(Conversion.commission), 0)).where(Conversion.content_id.in_(content_ids))
        )
        or 0
    )
    cost = Decimal(
        db.scalar(select(func.coalesce(func.sum(Cost.amount), 0)).where(Cost.content_id.in_(content_ids))) or 0
    )
    return {"impressions": impressions, "clicks": clicks, "conversions": conversions, "revenue": revenue, "cost": cost}


def _best_program(db: Session, product: Product) -> tuple[AffiliateProgram | None, AffiliateProgramScore | None]:
    candidates = [
        row
        for row in db.scalars(select(AffiliateProgram).where(AffiliateProgram.country == "US")).all()
        if row.status in {"eligible", "approved"}
        and (row.merchant == product.merchant.name or product.category in (row.categories or []))
    ]
    ranked: list[tuple[Decimal, AffiliateProgram, AffiliateProgramScore | None]] = []
    for program in candidates:
        score = db.scalar(
            select(AffiliateProgramScore)
            .where(AffiliateProgramScore.program_id == program.id)
            .order_by(AffiliateProgramScore.calculated_at.desc())
            .limit(1)
        )
        evaluation = score_affiliate_program(program, category=product.category)
        ranked.append((evaluation.score, program, score))
    if not ranked:
        return None, None
    _, program, score = max(ranked, key=lambda item: item[0])
    return program, score


def calculate_product_opportunity(db: Session, deal: Deal, settings: Settings) -> ProductOpportunity:
    seed_seo_taxonomy(db, settings)
    product = deal.product
    keyword_pair = db.execute(
        select(ProductKeyword, Keyword)
        .join(Keyword, Keyword.id == ProductKeyword.keyword_id)
        .where(ProductKeyword.product_id == product.id)
        .order_by(
            (ProductKeyword.product_match + Keyword.commercial_intent_score + Keyword.purchase_intent_score).desc()
        )
        .limit(1)
    ).first()
    if keyword_pair is None:
        raise ValueError(f"No keyword opportunity for product {product.id}")
    product_keyword, keyword = keyword_pair
    cluster = db.scalar(
        select(KeywordCluster)
        .join(KeywordClusterMember, KeywordClusterMember.cluster_id == KeywordCluster.id)
        .where(KeywordClusterMember.keyword_id == keyword.id)
        .order_by(KeywordClusterMember.relevance.desc())
        .limit(1)
    )
    board, board_score = select_board(db, product=product, keywords=[keyword], intent=keyword.intent)
    problem = db.scalar(select(ProductProblem).where(ProductProblem.product_id == product.id).limit(1))
    program, stored_program_score = _best_program(db, product)
    program_evaluation = score_affiliate_program(program, category=product.category) if program else None
    history = _historical_product_metrics(db, product)
    impressions = int(history["impressions"])
    clicks = int(history["clicks"])
    conversions = int(history["conversions"])
    revenue = Decimal(history["revenue"])
    observed_ctr = Decimal(clicks) / impressions if impressions else Decimal("0")
    observed_conversion = Decimal(conversions) / clicks if clicks else Decimal("0")
    intent_ctr = (
        Decimal("0.024") if keyword.intent in {"deal", "budget", "comparison", "purchase_intent"} else Decimal("0.016")
    )
    intent_conversion = (
        Decimal("0.045") if keyword.intent in {"comparison", "purchase_intent", "brand_specific"} else Decimal("0.032")
    )
    ctr_weight = min(Decimal("0.75"), Decimal(impressions) / Decimal("2000"))
    conversion_weight = min(Decimal("0.75"), Decimal(clicks) / Decimal("100"))
    expected_ctr = observed_ctr * ctr_weight + intent_ctr * (Decimal("1") - ctr_weight)
    expected_conversion = observed_conversion * conversion_weight + intent_conversion * (
        Decimal("1") - conversion_weight
    )
    expected_impressions = int(450 + float(keyword.search_relevance + keyword.trend_score) * 6)
    order_value = (
        Decimal(program.average_order_value)
        if program and program.average_order_value
        else Decimal(product.current_price)
    )
    commission_rate = Decimal(program.commission_rate) if program else Decimal(product.expected_commission_rate)
    expected_cost = settings.estimated_media_cost_per_content + settings.infrastructure_cost_per_content
    economics = expected_profit_model(
        impressions=1000,
        ctr=expected_ctr,
        conversion_rate=expected_conversion,
        average_order_value=order_value,
        commission_rate=commission_rate,
        estimated_cost=expected_cost,
    )
    expected_revenue = economics["expected_revenue"]
    expected_profit = economics["expected_profit"]
    historical_score = min(
        Decimal("100"),
        (revenue / clicks * Decimal("25") if clicks else Decimal("25")) + (Decimal(conversions) * Decimal("8")),
    )
    problem_score = Decimal(problem.relevance_score) if problem else Decimal("35")
    content_potential = problem_score * Decimal("0.65") + (
        Decimal("95") if product.authorized_image_urls else Decimal("65")
    ) * Decimal("0.35")
    affiliate_score = (
        Decimal(stored_program_score.attractiveness_score)
        if stored_program_score
        else program_evaluation.score
        if program_evaluation
        else min(Decimal("100"), Decimal(product.expected_commission_rate) * Decimal("1000"))
    )
    search_demand = (Decimal(keyword.search_relevance) + Decimal(keyword.trend_score)) / Decimal("2")
    commercial = (Decimal(keyword.commercial_intent_score) + Decimal(keyword.purchase_intent_score)) / Decimal("2")
    saturation = saturation_penalty(db, product)
    competition = Decimal(keyword.competition_estimate)
    risk = Decimal("0")
    if product.availability != "in_stock":
        risk += Decimal("50")
    if not program:
        risk += Decimal("12")
    elif program.pinterest_allowed is not True:
        risk += Decimal("20")
    if program and program.media_rights in {"unknown", "restricted"}:
        risk += Decimal("15")
    config = load_seo_taxonomy(settings.seo_taxonomy_path)
    raw_weights = config.get("opportunity_weights", {})
    weights = {key: Decimal(str(value)) for key, value in raw_weights.items()}
    components = {
        "deal_quality": Decimal(deal.deal_score),
        "search_demand": search_demand,
        "commercial_intent": commercial,
        "affiliate_economics": affiliate_score,
        "content_potential": content_potential,
        "historical_performance": historical_score,
        "problem_solution": problem_score,
    }
    positive = sum((components[key] * weights.get(key, Decimal("0")) for key in components), Decimal("0"))
    opportunity_score = max(
        Decimal("0"),
        min(
            Decimal("100"),
            positive - competition * Decimal("0.08") - saturation * Decimal("0.10") - risk * Decimal("0.10"),
        ),
    ).quantize(Decimal("0.01"), ROUND_HALF_UP)
    sample_confidence = min(Decimal("30"), Decimal(impressions) / Decimal("100")) + min(
        Decimal("20"), Decimal(conversions) * Decimal("5")
    )
    external_confidence = (
        Decimal(stored_program_score.confidence)
        if stored_program_score
        else program_evaluation.confidence
        if program_evaluation
        else Decimal("35")
    )
    confidence = min(
        Decimal("100"),
        sample_confidence + Decimal(keyword.confidence) * Decimal("0.3") + external_confidence * Decimal("0.3"),
    ).quantize(Decimal("0.01"))
    uncertainty = (Decimal("1") - confidence / Decimal("100")) * Decimal("0.70")
    low = max(Decimal("0"), expected_profit * (Decimal("1") - uncertainty)).quantize(Decimal("0.01"))
    high = max(low, expected_profit * (Decimal("1") + uncertainty)).quantize(Decimal("0.01"))
    rank_basis = (
        "expected_profit" if confidence >= settings.opportunity_profit_confidence_threshold else "opportunity_score"
    )
    reason = (
        f"Selected for {keyword.keyword} ({keyword.intent}); expected profit ${expected_profit}/1K at "
        f"{confidence}% confidence. Board match {board.name} scored {board_score['relevance_score']:.1f}."
    )
    row = ProductOpportunity(
        product_id=product.id,
        affiliate_program_id=program.id if program else None,
        keyword_cluster_id=cluster.id if cluster else None,
        board_id=board.id,
        weights_version=int(config.get("version", 1)),
        opportunity_score=opportunity_score,
        rank_basis=rank_basis,
        components={
            **{key: float(value.quantize(Decimal("0.01"))) for key, value in components.items()},
            "competition_penalty": float(competition * Decimal("0.08")),
            "saturation_penalty": float(saturation),
            "risk_penalty": float(risk),
            "primary_keyword": keyword.keyword,
            "search_intent": keyword.intent,
            "board_relevance": board_score,
            "historical": {
                key: float(value) if isinstance(value, Decimal) else value for key, value in history.items()
            },
        },
        expected_impressions=expected_impressions,
        expected_ctr=expected_ctr,
        expected_conversion_rate=expected_conversion,
        expected_order_value=order_value,
        commission_rate=commission_rate,
        expected_revenue_per_1000=expected_revenue.quantize(Decimal("0.01")),
        expected_cost_per_1000=expected_cost,
        expected_profit_per_1000=expected_profit,
        expected_profit_low=low,
        expected_profit_high=high,
        confidence=confidence,
        price_band=price_band(Decimal(product.current_price)),
        discount_band=discount_band(Decimal(product.discount_percent)),
        saturation_penalty=saturation,
        risk_penalty=risk,
        recommended_angle=f"{keyword.intent.replace('_', ' ')}: {problem.solution if problem else product.description}",
        selection_reason=reason,
    )
    db.add(row)
    db.commit()
    return row


def refresh_opportunities(db: Session, settings: Settings) -> list[ProductOpportunity]:
    rows: list[ProductOpportunity] = []
    deals = db.scalars(select(Deal).where(Deal.status == "active")).all()
    for deal in deals:
        rows.append(calculate_product_opportunity(db, deal, settings))
    return rows


def opportunity_feed(db: Session) -> list[dict[str, Any]]:
    latest_ids = (
        select(ProductOpportunity.product_id, func.max(ProductOpportunity.calculated_at).label("latest"))
        .group_by(ProductOpportunity.product_id)
        .subquery()
    )
    rows = db.scalars(
        select(ProductOpportunity)
        .join(
            latest_ids,
            (ProductOpportunity.product_id == latest_ids.c.product_id)
            & (ProductOpportunity.calculated_at == latest_ids.c.latest),
        )
        .order_by(
            ProductOpportunity.rank_basis.desc(),
            ProductOpportunity.expected_profit_per_1000.desc(),
            ProductOpportunity.opportunity_score.desc(),
        )
    ).all()
    result: list[dict[str, Any]] = []
    for row in rows:
        product = db.get(Product, row.product_id)
        program = db.get(AffiliateProgram, row.affiliate_program_id) if row.affiliate_program_id else None
        cluster = db.get(KeywordCluster, row.keyword_cluster_id) if row.keyword_cluster_id else None
        board = db.get(PinterestBoard, row.board_id) if row.board_id else None
        if not product:
            continue
        stats = (
            db.scalar(
                select(Deal.price_statistics)
                .where(Deal.product_id == product.id, Deal.status == "active")
                .order_by(Deal.created_at.desc())
                .limit(1)
            )
            or {}
        )
        result.append(
            {
                "id": row.id,
                "product_id": product.id,
                "product": product.product_name,
                "category": product.category,
                "merchant": product.merchant.name,
                "current_price": float(product.current_price),
                "average_30d": stats.get("average_30d"),
                "observed_low": stats.get("observed_all_time_low"),
                "discount_percent": float(product.discount_percent),
                "affiliate_program": program.program_name if program else "Product feed estimate",
                "commission_rate": float(row.commission_rate),
                "estimated_commission_per_sale": float(row.expected_order_value * row.commission_rate),
                "search_intent_score": row.components.get("commercial_intent"),
                "seo_opportunity": row.components.get("search_demand"),
                "expected_impressions": row.expected_impressions,
                "expected_ctr": float(row.expected_ctr),
                "expected_conversion_rate": float(row.expected_conversion_rate),
                "expected_epc": float(row.expected_conversion_rate * row.expected_order_value * row.commission_rate),
                "expected_profit_per_1000": float(row.expected_profit_per_1000),
                "expected_profit_low": float(row.expected_profit_low),
                "expected_profit_high": float(row.expected_profit_high),
                "opportunity_score": float(row.opportunity_score),
                "confidence": float(row.confidence),
                "rank_basis": row.rank_basis,
                "price_band": row.price_band,
                "discount_band": row.discount_band,
                "saturation_penalty": float(row.saturation_penalty),
                "risk_penalty": float(row.risk_penalty),
                "recommended_content_angle": row.recommended_angle,
                "recommended_keyword_cluster": cluster.name if cluster else None,
                "recommended_board": board.name if board else None,
                "selection_reason": row.selection_reason,
                "score_breakdown": row.components,
            }
        )
    result.sort(
        key=lambda item: (
            item["rank_basis"] == "expected_profit",
            item["expected_profit_per_1000"] if item["rank_basis"] == "expected_profit" else item["opportunity_score"],
        ),
        reverse=True,
    )
    return result


def evaluate_watchlists(db: Session) -> dict[str, int]:
    triggered = evaluated = 0
    for watch in db.scalars(select(ProductWatchlist).where(ProductWatchlist.status == "active")).all():
        products_query = select(Product)
        if watch.product_id:
            products_query = products_query.where(Product.id == watch.product_id)
        if watch.merchant_id:
            products_query = products_query.where(Product.merchant_id == watch.merchant_id)
        if watch.category:
            products_query = products_query.where(Product.category == watch.category)
        values: list[Decimal] = []
        for product in db.scalars(products_query).all():
            if watch.rule_type == "price_below_30d_percent":
                deal = db.scalar(select(Deal).where(Deal.product_id == product.id, Deal.status == "active"))
                values.append(Decimal(str((deal.price_statistics if deal else {}).get("percent_below_30d_average", 0))))
            elif watch.rule_type == "opportunity_score_above":
                opportunity = db.scalar(
                    select(ProductOpportunity)
                    .where(ProductOpportunity.product_id == product.id)
                    .order_by(ProductOpportunity.calculated_at.desc())
                    .limit(1)
                )
                values.append(Decimal(opportunity.opportunity_score) if opportunity else Decimal("0"))
            elif watch.rule_type == "commission_rate_above":
                values.append(Decimal(product.expected_commission_rate) * Decimal("100"))
        value = max(values, default=Decimal("0"))
        watch.last_value = value
        watch.last_evaluated_at = datetime.now(UTC)
        evaluated += 1
        if value >= Decimal(watch.threshold):
            watch.status = "triggered"
            watch.triggered_at = datetime.now(UTC)
            triggered += 1
    db.commit()
    return {"evaluated": evaluated, "triggered": triggered}


def reset_demo_opportunities(db: Session) -> None:
    db.execute(delete(ProductOpportunity))
    db.commit()
