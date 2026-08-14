from __future__ import annotations

import csv
import io
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.db.models import (
    AIUsage,
    Click,
    ContentBrief,
    ContentIdea,
    ContentKeyword,
    ContentVariant,
    Conversion,
    Cost,
    Deal,
    Keyword,
    KeywordPerformance,
    PerformanceEvent,
    PinterestBoard,
    Product,
    Publication,
)


def _since(days: int | None) -> datetime | None:
    return datetime.now(UTC) - timedelta(days=days) if days is not None else None


def metric_snapshot(db: Session, days: int | None) -> dict[str, Any]:
    since = _since(days)
    pub_filters = [Publication.published_at >= since] if since else []
    event_filters = [PerformanceEvent.occurred_at >= since] if since else []
    click_filters = [Click.clicked_at >= since] if since else []
    conversion_filters = [Conversion.converted_at >= since] if since else []
    cost_filters = [Cost.incurred_at >= since] if since else []
    ai_filters = [AIUsage.occurred_at >= since] if since else []
    posts = int(db.scalar(select(func.count(Publication.id)).where(*pub_filters)) or 0)
    impressions = int(
        db.scalar(
            select(func.coalesce(func.sum(PerformanceEvent.count), 0)).where(
                PerformanceEvent.event_type == "impression", *event_filters
            )
        )
        or 0
    )
    clicks = int(db.scalar(select(func.count(Click.id)).where(*click_filters)) or 0)
    conversions = int(db.scalar(select(func.count(Conversion.id)).where(*conversion_filters)) or 0)
    revenue = Decimal(
        db.scalar(select(func.coalesce(func.sum(Conversion.commission), 0)).where(*conversion_filters)) or 0
    )
    operating_cost = Decimal(db.scalar(select(func.coalesce(func.sum(Cost.amount), 0)).where(*cost_filters)) or 0)
    ai_cost = Decimal(db.scalar(select(func.coalesce(func.sum(AIUsage.estimated_cost), 0)).where(*ai_filters)) or 0)
    ad_spend = Decimal(
        db.scalar(select(func.coalesce(func.sum(Cost.amount), 0)).where(Cost.kind == "advertising", *cost_filters)) or 0
    )
    total_cost = operating_cost + ai_cost
    profit = revenue - total_cost
    ctr = Decimal(clicks) / impressions if impressions else Decimal("0")
    conversion_rate = Decimal(conversions) / clicks if clicks else Decimal("0")
    return {
        "posts": posts,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": float(ctr),
        "conversions": conversions,
        "conversion_rate": float(conversion_rate),
        "affiliate_revenue": float(revenue),
        "ai_cost": float(ai_cost),
        "operating_cost": float(operating_cost),
        "advertising_spend": float(ad_spend),
        "gross_profit": float(profit),
        "roas": float(revenue / ad_spend) if ad_spend else 0,
        "profit_per_post": float(profit / posts) if posts else 0,
        "revenue_per_1000_impressions": float(revenue / impressions * 1000) if impressions else 0,
        "earnings_per_outbound_click": float(revenue / clicks) if clicks else 0,
    }


def overview(db: Session) -> dict[str, Any]:
    return {
        "today": metric_snapshot(db, 1),
        "days_7": metric_snapshot(db, 7),
        "days_30": metric_snapshot(db, 30),
        "lifetime": metric_snapshot(db, None),
    }


def rankings(db: Session) -> dict[str, list[dict[str, Any]]]:
    templates = db.execute(
        select(ContentVariant.template_key, func.count(ContentVariant.id).label("posts"))
        .group_by(ContentVariant.template_key)
        .order_by(func.count(ContentVariant.id).desc())
        .limit(5)
    ).all()
    hooks = db.execute(
        select(ContentIdea.hook, func.count(ContentVariant.id).label("variants"))
        .join(ContentVariant, ContentVariant.idea_id == ContentIdea.id)
        .group_by(ContentIdea.hook)
        .order_by(func.count(ContentVariant.id).desc())
        .limit(5)
    ).all()
    return {
        "top_templates": [{"template": row.template_key, "posts": row.posts} for row in templates],
        "top_hooks": [{"hook": row.hook, "variants": row.variants} for row in hooks],
    }


def weekly_business_report(db: Session) -> dict[str, Any]:
    metrics = metric_snapshot(db, 7)
    ranked = rankings(db)
    top_template = ranked["top_templates"][0]["template"] if ranked["top_templates"] else None
    failures = [
        "Insufficient attributed conversion data; avoid large scoring-weight changes."
        if metrics["conversions"] < 20
        else "Review the bottom-quartile content and retire repeated low-profit formats."
    ]
    recommendations = [
        f"Keep testing {top_template} while it leads observed volume."
        if top_template
        else "Publish enough approved variants to establish a template baseline.",
        "Prioritize earnings per click and gross profit over raw impressions.",
    ]
    return {
        "period": "last_7_days",
        "revenue": metrics["affiliate_revenue"],
        "costs": metrics["operating_cost"] + metrics["ai_cost"],
        "profit": metrics["gross_profit"],
        "top_content": ranked["top_hooks"],
        "top_templates": ranked["top_templates"],
        "biggest_failures": failures,
        "experiments": [],
        "recommended_changes": recommendations,
        "evidence": metrics,
    }


def import_conversion_csv(db: Session, raw: bytes, provider: str = "csv") -> dict[str, int]:
    if len(raw) > 5_000_000:
        raise ValueError("Conversion CSV exceeds 5 MB")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    required = {"external_id", "converted_at", "order_value", "commission", "currency"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ValueError(f"Required columns: {', '.join(sorted(required))}")
    imported = skipped = 0
    for row in reader:
        exists = db.scalar(
            select(Conversion).where(Conversion.provider == provider, Conversion.external_id == row["external_id"])
        )
        if exists:
            skipped += 1
            continue
        converted_at = datetime.fromisoformat(row["converted_at"].replace("Z", "+00:00"))
        db.add(
            Conversion(
                provider=provider,
                external_id=row["external_id"],
                product_id=row.get("product_id") or None,
                content_id=row.get("content_id") or None,
                campaign=row.get("campaign") or None,
                order_value=Decimal(row["order_value"]),
                commission=Decimal(row["commission"]),
                currency=row["currency"].upper(),
                converted_at=converted_at,
            )
        )
        imported += 1
    db.commit()
    return {"imported": imported, "skipped": skipped}


def _content_metrics(db: Session, content_ids: list[str]) -> dict[str, Decimal | int]:
    if not content_ids:
        return {
            "posts": 0,
            "impressions": 0,
            "clicks": 0,
            "conversions": 0,
            "revenue": Decimal("0"),
            "cost": Decimal("0"),
        }
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
    return {
        "posts": len(set(content_ids)),
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "revenue": revenue,
        "cost": cost,
    }


def _performance_payload(label: str, metrics: dict[str, Decimal | int]) -> dict[str, Any]:
    impressions = int(metrics["impressions"])
    clicks = int(metrics["clicks"])
    conversions = int(metrics["conversions"])
    revenue = Decimal(metrics["revenue"])
    cost = Decimal(metrics["cost"])
    profit = revenue - cost
    return {
        "label": label,
        "posts": int(metrics["posts"]),
        "impressions": impressions,
        "clicks": clicks,
        "ctr": float(Decimal(clicks) / impressions) if impressions else 0,
        "conversions": conversions,
        "conversion_rate": float(Decimal(conversions) / clicks) if clicks else 0,
        "revenue": float(revenue),
        "cost": float(cost),
        "profit": float(profit),
        "epc": float(revenue / clicks) if clicks else 0,
        "revenue_per_1000_impressions": float(revenue / impressions * 1000) if impressions else 0,
        "profit_per_1000_impressions": float(profit / impressions * 1000) if impressions else 0,
        "profit_per_pin": float(profit / int(metrics["posts"])) if int(metrics["posts"]) else 0,
    }


def keyword_performance_report(db: Session, *, persist: bool = False) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    now = datetime.now(UTC)
    for keyword in db.scalars(select(Keyword).order_by(Keyword.keyword)).all():
        content_ids = list(
            db.scalars(select(ContentKeyword.content_id).where(ContentKeyword.keyword_id == keyword.id)).all()
        )
        metrics = _content_metrics(db, content_ids)
        payload = _performance_payload(keyword.keyword, metrics)
        sample = min(
            Decimal("100"), Decimal(payload["impressions"]) / Decimal("20") + Decimal(payload["conversions"]) * 10
        )
        profit_signal = max(
            Decimal("0"), min(Decimal("100"), Decimal(str(payload["profit_per_1000_impressions"])) * 5 + 40)
        )
        keyword.performance_score = (
            profit_signal * Decimal("0.55")
            + Decimal(str(payload["ctr"])) * Decimal("100") * Decimal("0.15")
            + Decimal(str(payload["conversion_rate"])) * Decimal("100") * Decimal("0.20")
            + sample * Decimal("0.10")
        ).quantize(Decimal("0.01"))
        payload.update(
            {
                "keyword_id": keyword.id,
                "intent": keyword.intent,
                "performance_score": float(keyword.performance_score),
                "confidence": float(sample),
            }
        )
        rows.append(payload)
        if persist and content_ids:
            db.add(
                KeywordPerformance(
                    keyword_id=keyword.id,
                    content_id=None,
                    impressions=int(metrics["impressions"]),
                    clicks=int(metrics["clicks"]),
                    conversions=int(metrics["conversions"]),
                    revenue=Decimal(metrics["revenue"]),
                    cost=Decimal(metrics["cost"]),
                    profit=Decimal(metrics["revenue"]) - Decimal(metrics["cost"]),
                    period_start=now - timedelta(days=30),
                    period_end=now,
                    confidence=sample,
                )
            )
    db.commit()
    return sorted(rows, key=lambda item: (item["profit"], item["conversions"], item["clicks"]), reverse=True)


def _band_report(db: Session, *, dimension: str) -> list[dict[str, Any]]:
    buckets: dict[str, list[str]] = {}
    rows = db.execute(
        select(ContentVariant.id, Product.current_price, Product.discount_percent)
        .join(ContentIdea, ContentIdea.id == ContentVariant.idea_id)
        .join(Deal, Deal.id == ContentIdea.deal_id)
        .join(Product, Product.id == Deal.product_id)
    ).all()
    for content_id, price, discount in rows:
        value = Decimal(price if dimension == "price" else discount)
        if dimension == "price":
            label = (
                "$0–25"
                if value < 25
                else "$25–50"
                if value < 50
                else "$50–100"
                if value < 100
                else "$100–250"
                if value < 250
                else "$250+"
            )
        else:
            label = (
                "0–10%"
                if value < 10
                else "10–20%"
                if value < 20
                else "20–30%"
                if value < 30
                else "30–40%"
                if value < 40
                else "40%+"
            )
        buckets.setdefault(label, []).append(content_id)
    return sorted(
        [_performance_payload(label, _content_metrics(db, ids)) for label, ids in buckets.items()],
        key=lambda item: item["profit_per_1000_impressions"],
        reverse=True,
    )


def seo_commercial_analytics(db: Session) -> dict[str, Any]:
    content_type_rows = db.execute(
        select(ContentVariant.id, ContentBrief.content_type)
        .join(ContentIdea, ContentIdea.id == ContentVariant.idea_id)
        .join(ContentBrief, ContentBrief.idea_id == ContentIdea.id)
    ).all()
    content_types: dict[str, list[str]] = {}
    for content_id, content_type in content_type_rows:
        content_types.setdefault(content_type, []).append(content_id)
    return {
        "keywords": keyword_performance_report(db),
        "price_bands": _band_report(db, dimension="price"),
        "discount_bands": _band_report(db, dimension="discount"),
        "content_types": [
            _performance_payload(label, _content_metrics(db, ids)) for label, ids in content_types.items()
        ],
    }


def refresh_board_performance(db: Session) -> int:
    updated = 0
    for board in db.scalars(select(PinterestBoard)).all():
        content_ids = list(
            db.scalars(
                select(ContentVariant.id)
                .join(ContentIdea, ContentIdea.id == ContentVariant.idea_id)
                .join(ContentBrief, ContentBrief.idea_id == ContentIdea.id)
                .where(ContentBrief.board_id == board.id)
            ).all()
        )
        metrics = _content_metrics(db, content_ids)
        impressions = int(metrics["impressions"])
        clicks = int(metrics["clicks"])
        board.historical_profit_per_1000 = (
            (Decimal(metrics["revenue"]) - Decimal(metrics["cost"])) / impressions * 1000
            if impressions
            else Decimal("0")
        )
        board.historical_conversion_rate = Decimal(int(metrics["conversions"])) / clicks if clicks else Decimal("0")
        updated += 1
    db.commit()
    return updated


def weekly_search_strategy_report(db: Session) -> dict[str, Any]:
    analytics = seo_commercial_analytics(db)
    keywords = [row for row in analytics["keywords"] if row["impressions"] > 0]
    price_bands = [row for row in analytics["price_bands"] if row["impressions"] > 0]
    discount_bands = [row for row in analytics["discount_bands"] if row["impressions"] > 0]
    insights: list[str] = []
    if keywords:
        top_profit = max(keywords, key=lambda row: row["profit_per_1000_impressions"])
        top_epc = max(keywords, key=lambda row: row["epc"])
        insights.extend(
            [
                (
                    f"'{top_profit['label']}' led observed profit per 1,000 impressions at "
                    f"${top_profit['profit_per_1000_impressions']:.2f}."
                ),
                f"'{top_epc['label']}' led observed earnings per click at ${top_epc['epc']:.2f}.",
            ]
        )
    if price_bands:
        top_band = price_bands[0]
        insights.append(
            f"The {top_band['label']} price band led observed profit per 1,000 impressions at "
            f"${top_band['profit_per_1000_impressions']:.2f}."
        )
    if discount_bands:
        top_discount = discount_bands[0]
        insights.append(
            f"The {top_discount['label']} discount band led observed profit; discount depth "
            "alone is not the ranking target."
        )
    if not insights:
        insights.append(
            "Insufficient keyword-attributed traffic; continue controlled publishing before changing weights."
        )
    sample_impressions = sum(row["impressions"] for row in keywords)
    sample_conversions = sum(row["conversions"] for row in keywords)
    return {
        "period": "observed_lifetime_with_30_day_learning_snapshot",
        "optimization_target": "attributable_profit",
        "insights": insights,
        "recommendations": [
            "Increase allocation only for clusters with conversion evidence and positive profit per 1,000 impressions.",
            "Keep changes within 15% while keyword conversion samples remain small.",
            "Refresh Pinterest Trends inputs before treating configured trend scores as live demand.",
        ],
        "minimum_sample_guard": {
            "observed_impressions": sample_impressions,
            "observed_conversions": sample_conversions,
            "decision_ready": sample_impressions >= 1000 and sample_conversions >= 5,
        },
        "evidence": analytics,
        "generated_deterministically": True,
    }
