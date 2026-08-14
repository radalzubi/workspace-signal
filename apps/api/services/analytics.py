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
    ContentIdea,
    ContentVariant,
    Conversion,
    Cost,
    PerformanceEvent,
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
