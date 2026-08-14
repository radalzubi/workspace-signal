from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.db.models import (
    Click,
    ContentVariant,
    PerformanceEvent,
    Publication,
    StrategySnapshot,
)
from apps.api.services.analytics import metric_snapshot, rankings
from apps.api.services.scoring import DEFAULT_WEIGHTS


def detect_winners(db: Session) -> dict[str, int]:
    changed = {"winner": 0, "promising": 0, "declining": 0}
    variants = db.scalars(select(ContentVariant)).all()
    for variant in variants:
        publication = db.scalar(select(Publication).where(Publication.content_id == variant.id))
        if not publication:
            continue
        impressions = int(
            db.scalar(
                select(func.coalesce(func.sum(PerformanceEvent.count), 0)).where(
                    PerformanceEvent.publication_id == publication.id,
                    PerformanceEvent.event_type == "impression",
                )
            )
            or 0
        )
        clicks = int(db.scalar(select(func.count(Click.id)).where(Click.content_id == variant.id)) or 0)
        ctr = Decimal(clicks) / impressions if impressions else Decimal("0")
        target = (
            "winner"
            if impressions >= 500 and ctr >= Decimal("0.025")
            else "promising"
            if ctr >= Decimal("0.015")
            else "testing"
        )
        if impressions >= 1000 and ctr < Decimal("0.005"):
            target = "declining"
        if target != variant.winner_state:
            variant.winner_state = target
            if target in changed:
                changed[target] += 1
    db.commit()
    return changed


def create_daily_strategy(db: Session) -> StrategySnapshot:
    metrics = metric_snapshot(db, 30)
    rank = rankings(db)
    weights = {key: float(value) for key, value in DEFAULT_WEIGHTS.items()}
    best_template = rank["top_templates"][0]["template"] if rank["top_templates"] else "deal_alert"
    summary = (
        f"Keep scoring changes bounded. The current top observed template is {best_template}. "
        f"30-day CTR is {metrics['ctr']:.2%}; gross profit is ${metrics['gross_profit']:.2f}. "
        "Validate with more conversion data before shifting any weight by more than 5%."
    )
    prior = db.scalar(select(StrategySnapshot).order_by(StrategySnapshot.created_at.desc()).limit(1))
    snapshot = StrategySnapshot(
        summary=summary,
        metrics={**metrics, **rank},
        scoring_weights=weights,
        previous_snapshot_id=prior.id if prior else None,
    )
    db.add(snapshot)
    db.commit()
    return snapshot
