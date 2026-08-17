from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime

from celery.utils.log import get_task_logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import get_settings
from apps.api.db.models import ContentVariant, Deal, JobRun
from apps.api.db.session import SessionLocal
from apps.api.services.affiliate import ensure_affiliate_link
from apps.api.services.analytics import keyword_performance_report, refresh_board_performance
from apps.api.services.case_lantern import create_pilot_story, validate_story
from apps.api.services.deals import detect_deals
from apps.api.services.demo import bootstrap_demo
from apps.api.services.opportunities import evaluate_watchlists as evaluate_watchlist_rules
from apps.api.services.opportunities import refresh_opportunities
from apps.api.services.optimization import create_daily_strategy, detect_winners
from apps.api.services.publishing import publish_variant
from workers.celery_app import celery_app

logger = get_task_logger(__name__)
settings = get_settings()


def _start(name: str) -> tuple[Session, JobRun]:
    db = SessionLocal()
    run = JobRun(job_name=name, status="running")
    db.add(run)
    db.commit()
    return db, run


def _finish(
    db: Session,
    run: JobRun,
    detail: Mapping[str, object],
    error: Exception | None = None,
) -> None:
    run.status = "failed" if error else "succeeded"
    run.detail = {**detail, **({"error": str(error)[:1000]} if error else {})}
    run.completed_at = datetime.now(UTC)
    db.commit()
    db.close()


@celery_app.task(name="workers.tasks.product_sync")  # type: ignore[untyped-decorator]
def product_sync() -> dict[str, object]:
    db, run = _start("product_sync")
    try:
        if settings.demo_mode:
            result: dict[str, object] = {key: value for key, value in bootstrap_demo(db, settings).items()}
        else:
            result = {"status": "provider_not_configured"}
            detect_deals(db, settings)
        _finish(db, run, result)
        return result
    except Exception as exc:
        _finish(db, run, {}, exc)
        raise


@celery_app.task(name="workers.tasks.publish_due")  # type: ignore[untyped-decorator]
def publish_due() -> dict[str, int]:
    db, run = _start("publish_due")
    published = 0
    try:
        variants = db.scalars(
            select(ContentVariant).where(
                ContentVariant.status == "scheduled",
                ContentVariant.scheduled_for <= datetime.now(UTC),
            )
        ).all()
        for variant in variants:
            link = ensure_affiliate_link(db, variant, settings)
            publish_variant(db, variant, link, settings)
            published += 1
        result = {"published": published}
        _finish(db, run, result)
        return result
    except Exception as exc:
        _finish(db, run, {"published": published}, exc)
        raise


@celery_app.task(name="workers.tasks.revalidate_deals")  # type: ignore[untyped-decorator]
def revalidate_deals() -> dict[str, int]:
    db, run = _start("revalidate_deals")
    flagged = 0
    try:
        for deal in db.scalars(select(Deal).where(Deal.status == "active")).all():
            if deal.expires_at <= datetime.now(UTC) or deal.product.availability != "in_stock":
                deal.status = "expired"
                flagged += 1
        db.commit()
        result = {"flagged": flagged}
        _finish(db, run, result)
        return result
    except Exception as exc:
        _finish(db, run, {"flagged": flagged}, exc)
        raise


@celery_app.task(name="workers.tasks.daily_optimization")  # type: ignore[untyped-decorator]
def daily_optimization() -> dict[str, object]:
    db, run = _start("daily_optimization")
    try:
        changes = detect_winners(db)
        snapshot = create_daily_strategy(db)
        result: dict[str, object] = {
            "winner_changes": changes,
            "strategy_id": snapshot.id,
        }
        _finish(db, run, result)
        return result
    except Exception as exc:
        _finish(db, run, {}, exc)
        raise


@celery_app.task(name="workers.tasks.seo_commercial_learning")  # type: ignore[untyped-decorator]
def seo_commercial_learning() -> dict[str, object]:
    db, run = _start("seo_commercial_learning")
    try:
        keywords = keyword_performance_report(db, persist=True)
        boards = refresh_board_performance(db)
        opportunities = refresh_opportunities(db, settings)
        result: dict[str, object] = {
            "keywords_analyzed": len(keywords),
            "boards_updated": boards,
            "opportunities_scored": len(opportunities),
            "optimization_target": "attributable_profit",
        }
        _finish(db, run, result)
        return result
    except Exception as exc:
        _finish(db, run, {}, exc)
        raise


@celery_app.task(name="workers.tasks.evaluate_watchlists")  # type: ignore[untyped-decorator]
def evaluate_watchlists() -> dict[str, int]:
    db, run = _start("evaluate_watchlists")
    try:
        result = evaluate_watchlist_rules(db)
        _finish(db, run, result)
        return result
    except Exception as exc:
        _finish(db, run, {}, exc)
        raise


@celery_app.task(name="workers.tasks.case_lantern_daily_brief")  # type: ignore[untyped-decorator]
def case_lantern_daily_brief() -> dict[str, object]:
    """Create a sourced review item; never approve or publish it automatically."""
    db, run = _start("case_lantern_daily_brief")
    try:
        if not settings.case_lantern_enabled:
            result: dict[str, object] = {"status": "disabled", "created": 0}
        else:
            project = create_pilot_story(db, settings)
            report = validate_story(db, project, settings)
            project.quality_report = report
            db.commit()
            result = {
                "status": project.status,
                "created": 1,
                "story_id": project.id,
                "validation_passed": bool(report["passed"]),
                "human_approval_required": True,
                "public_auto_post": False,
            }
        _finish(db, run, result)
        return result
    except Exception as exc:
        _finish(db, run, {}, exc)
        raise
