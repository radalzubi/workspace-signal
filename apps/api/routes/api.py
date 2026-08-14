from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from apps.api.core.config import Settings, get_settings
from apps.api.core.crypto import encrypt_json
from apps.api.core.security import anonymize_visitor, require_admin
from apps.api.db.models import (
    AffiliateLink,
    AppSetting,
    Click,
    ContentBrief,
    ContentIdea,
    ContentVariant,
    Cost,
    Deal,
    Experiment,
    ExperimentKeyword,
    JobRun,
    Keyword,
    PinterestBoard,
    Product,
    ProductWatchlist,
    Publication,
    StrategySnapshot,
)
from apps.api.db.session import get_db
from apps.api.schemas import (
    AffiliateProgramInput,
    ContentOut,
    DealOut,
    OnboardingInput,
    ProductOut,
    QueueUpdate,
    UnitEconomicsInput,
    WatchlistInput,
)
from apps.api.services.affiliate import ensure_affiliate_link
from apps.api.services.affiliate_discovery import (
    affiliate_program_rows,
    discovery_source_catalog,
    persist_affiliate_programs,
    rescore_affiliate_programs,
)
from apps.api.services.analytics import (
    import_conversion_csv,
    keyword_performance_report,
    overview,
    rankings,
    seo_commercial_analytics,
    weekly_business_report,
    weekly_search_strategy_report,
)
from apps.api.services.demo import bootstrap_demo
from apps.api.services.economics import calculate_unit_economics
from apps.api.services.opportunities import evaluate_watchlists, opportunity_feed, refresh_opportunities
from apps.api.services.optimization import create_daily_strategy, detect_winners
from apps.api.services.publishing import PinterestPublisher, publish_variant
from apps.api.services.scheduler import schedule_approved
from apps.api.services.seo import keyword_experiment_result, keyword_summary, seo_taxonomy_summary

router = APIRouter()
admin = Annotated[None, Depends(require_admin)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "dealforge-api"}


@router.get("/ready")
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}


@router.get("/overview")
def get_overview(db: Session = Depends(get_db)) -> dict[str, Any]:
    return {**overview(db), **rankings(db)}


@router.get("/products", response_model=list[ProductOut])
def products(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.created_at.desc()).limit(limit)).all())


@router.get("/deals", response_model=list[DealOut])
def deals(db: Session = Depends(get_db)) -> list[Deal]:
    return list(db.scalars(select(Deal).options(selectinload(Deal.product)).order_by(Deal.deal_score.desc())).all())


@router.get("/content", response_model=list[ContentOut])
def content(status: str | None = None, db: Session = Depends(get_db)) -> list[ContentVariant]:
    query = select(ContentVariant).order_by(ContentVariant.created_at.desc())
    if status:
        query = query.where(ContentVariant.status == status)
    return list(db.scalars(query).all())


@router.get("/publications")
def publications(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(Publication).order_by(Publication.created_at.desc()).limit(100)).all()
    return [
        {
            "id": row.id,
            "content_id": row.content_id,
            "platform": row.platform,
            "status": row.status,
            "external_url": row.external_url,
            "published_at": row.published_at,
            "error": row.error,
        }
        for row in rows
    ]


@router.patch("/content/{content_id}", dependencies=[Depends(require_admin)])
def update_content(
    content_id: str,
    payload: QueueUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    variant = db.scalar(
        select(ContentVariant)
        .options(
            selectinload(ContentVariant.idea)
            .selectinload(ContentIdea.deal)
            .selectinload(Deal.product)
            .selectinload(Product.merchant)
        )
        .where(ContentVariant.id == content_id)
    )
    if variant is None:
        raise HTTPException(404, "Content not found")
    if payload.caption is not None:
        variant.caption = payload.caption
    if payload.action == "approve":
        variant.status = "approved"
        variant.approved_at = datetime.now(UTC)
    elif payload.action == "reject":
        variant.status = "rejected"
    elif payload.action == "schedule":
        if not payload.scheduled_for:
            raise HTTPException(422, "scheduled_for is required")
        variant.scheduled_for = payload.scheduled_for
        variant.status = "scheduled"
    elif payload.action == "regenerate":
        variant.status = "regeneration_requested"
    elif payload.action == "publish":
        link = ensure_affiliate_link(db, variant, settings)
        if payload.affiliate_url:
            link.affiliate_url = str(payload.affiliate_url)
            db.commit()
        try:
            publication = publish_variant(db, variant, link, settings)
        except (ValueError, PermissionError) as exc:
            raise HTTPException(409, str(exc)) from exc
        return {
            "content_id": variant.id,
            "status": variant.status,
            "publication_id": publication.id,
        }
    db.commit()
    return {"content_id": variant.id, "status": variant.status}


@router.post("/pipeline/run", dependencies=[Depends(require_admin)])
def run_pipeline(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict[str, int | str]:
    if not settings.demo_mode:
        raise HTTPException(409, "Live provider sync is executed by the worker adapter")
    return bootstrap_demo(db, settings)


@router.post("/schedule", dependencies=[Depends(require_admin)])
def schedule_queue(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)) -> dict[str, int]:
    return {"scheduled": schedule_approved(db, settings)}


@router.post("/conversions/import", dependencies=[Depends(require_admin)])
async def conversion_import(
    file: UploadFile = File(...), provider: str = "csv", db: Session = Depends(get_db)
) -> dict[str, int]:
    if file.content_type not in {
        "text/csv",
        "application/vnd.ms-excel",
        "application/octet-stream",
    }:
        raise HTTPException(415, "Upload a CSV file")
    try:
        return import_conversion_csv(db, await file.read(), provider)
    except (ValueError, UnicodeDecodeError) as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get("/costs")
def costs(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(Cost).order_by(Cost.incurred_at.desc()).limit(200)).all()
    return [
        {
            "id": row.id,
            "kind": row.kind,
            "amount": float(row.amount),
            "currency": row.currency,
            "incurred_at": row.incurred_at,
            "detail": row.detail,
        }
        for row in rows
    ]


@router.post("/costs", dependencies=[Depends(require_admin)])
def add_cost(kind: str, amount: Decimal, db: Session = Depends(get_db)) -> dict[str, str]:
    if amount < 0:
        raise HTTPException(422, "amount cannot be negative")
    row = Cost(kind=kind, amount=amount, detail={"source": "manual"})
    db.add(row)
    db.commit()
    return {"id": row.id}


@router.post("/unit-economics")
def unit_economics(payload: UnitEconomicsInput) -> dict[str, Decimal]:
    return calculate_unit_economics(payload)


@router.get("/experiments")
def experiments(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return [
        {
            "id": row.id,
            "name": row.name,
            "hypothesis": row.hypothesis,
            "status": row.status,
            "allocation": row.allocation,
            "result": row.result,
        }
        for row in db.scalars(select(Experiment).order_by(Experiment.created_at.desc())).all()
    ]


@router.get("/strategy")
def strategy(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(StrategySnapshot).order_by(StrategySnapshot.created_at.desc()).limit(30)).all()
    return [
        {
            "id": row.id,
            "summary": row.summary,
            "metrics": row.metrics,
            "scoring_weights": row.scoring_weights,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/reports/weekly")
def weekly_report(db: Session = Depends(get_db)) -> dict[str, Any]:
    return weekly_business_report(db)


@router.get("/reports/search-strategy")
def search_strategy_report(db: Session = Depends(get_db)) -> dict[str, Any]:
    return weekly_search_strategy_report(db)


@router.get("/seo/keywords")
def seo_keywords(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return keyword_summary(db, limit=limit)


@router.get("/seo/taxonomy")
def seo_taxonomy(db: Session = Depends(get_db)) -> dict[str, Any]:
    return seo_taxonomy_summary(db)


@router.get("/seo/analytics")
def seo_analytics(db: Session = Depends(get_db)) -> dict[str, Any]:
    return seo_commercial_analytics(db)


@router.get("/seo/content-briefs")
def content_briefs(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    briefs = db.scalars(select(ContentBrief).order_by(ContentBrief.created_at.desc()).limit(100)).all()
    output: list[dict[str, Any]] = []
    for brief in briefs:
        primary = db.get(Keyword, brief.primary_keyword_id)
        output.append(
            {
                "id": brief.id,
                "idea_id": brief.idea_id,
                "product_id": brief.product_id,
                "product": brief.idea.deal.product.product_name,
                "primary_keyword": primary.keyword if primary else None,
                "search_intent": brief.search_intent,
                "content_type": brief.content_type,
                "target_audience": brief.target_audience,
                "problem_solved": brief.problem_solved,
                "verified_product_facts": brief.verified_product_facts,
                "price_context": brief.price_context,
                "affiliate_economics": brief.affiliate_economics,
                "recommended_angle": brief.recommended_angle,
                "recommended_board": brief.board.name,
                "cta": brief.cta,
                "disclosure": brief.disclosure,
                "title_candidates": brief.title_candidates,
                "selected_title": brief.selected_title,
                "confidence": float(brief.confidence),
            }
        )
    return output


@router.get("/seo/experiments")
def seo_experiments(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[dict[str, Any]]:
    performance = {row["keyword_id"]: row for row in keyword_performance_report(db)}
    output: list[dict[str, Any]] = []
    for experiment in db.scalars(select(Experiment).order_by(Experiment.created_at.desc())).all():
        associations = db.execute(
            select(ExperimentKeyword, Keyword)
            .join(Keyword, Keyword.id == ExperimentKeyword.keyword_id)
            .where(ExperimentKeyword.experiment_id == experiment.id)
        ).all()
        if not associations:
            continue
        arms = [
            {
                "label": association.variant_label,
                "keyword": keyword.keyword,
                "impressions": performance.get(keyword.id, {}).get("impressions", 0),
                "clicks": performance.get(keyword.id, {}).get("clicks", 0),
                "conversions": performance.get(keyword.id, {}).get("conversions", 0),
                "revenue": performance.get(keyword.id, {}).get("revenue", 0),
                "profit": performance.get(keyword.id, {}).get("profit", 0),
            }
            for association, keyword in associations
        ]
        evaluation = keyword_experiment_result(
            arms,
            minimum_impressions=settings.seo_min_experiment_impressions,
            minimum_clicks=settings.seo_min_experiment_clicks,
            minimum_conversions=settings.seo_min_experiment_conversions,
        )
        output.append(
            {
                "id": experiment.id,
                "name": experiment.name,
                "hypothesis": experiment.hypothesis,
                "status": experiment.status,
                "arms": arms,
                "evaluation": evaluation,
            }
        )
    return output


@router.get("/opportunities")
def opportunities(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return opportunity_feed(db)


@router.post("/opportunities/refresh", dependencies=[Depends(require_admin)])
def refresh_opportunity_feed(
    db: Session = Depends(get_db), settings: Settings = Depends(get_settings)
) -> dict[str, int | str]:
    rows = refresh_opportunities(db, settings)
    return {"scored": len(rows), "optimization_target": "attributable_profit"}


@router.get("/affiliate-programs")
def affiliate_programs(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    return affiliate_program_rows(db)


@router.get("/affiliate-programs/discovery-sources")
def affiliate_discovery_sources() -> list[dict[str, Any]]:
    return discovery_source_catalog()


@router.post("/affiliate-programs/import", dependencies=[Depends(require_admin)])
def import_affiliate_programs(payload: list[AffiliateProgramInput], db: Session = Depends(get_db)) -> dict[str, int]:
    return {"imported": len(persist_affiliate_programs(db, payload))}


@router.post("/affiliate-programs/rescore", dependencies=[Depends(require_admin)])
def rescore_programs(db: Session = Depends(get_db)) -> dict[str, int]:
    return {"scored": rescore_affiliate_programs(db)}


@router.get("/watchlists")
def watchlists(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.scalars(select(ProductWatchlist).order_by(ProductWatchlist.created_at.desc())).all()
    return [
        {
            "id": row.id,
            "name": row.name,
            "product_id": row.product_id,
            "merchant_id": row.merchant_id,
            "category": row.category,
            "rule_type": row.rule_type,
            "threshold": float(row.threshold),
            "status": row.status,
            "last_value": float(row.last_value) if row.last_value is not None else None,
            "last_evaluated_at": row.last_evaluated_at,
            "triggered_at": row.triggered_at,
        }
        for row in rows
    ]


@router.post("/watchlists", dependencies=[Depends(require_admin)])
def create_watchlist(payload: WatchlistInput, db: Session = Depends(get_db)) -> dict[str, str]:
    if payload.product_id and db.get(Product, payload.product_id) is None:
        raise HTTPException(404, "Product not found")
    row = ProductWatchlist(**payload.model_dump())
    db.add(row)
    db.commit()
    return {"id": row.id, "status": row.status}


@router.post("/watchlists/evaluate", dependencies=[Depends(require_admin)])
def run_watchlist_evaluation(db: Session = Depends(get_db)) -> dict[str, int]:
    return evaluate_watchlists(db)


@router.patch("/seo/boards/{board_id}", dependencies=[Depends(require_admin)])
def link_pinterest_board(
    board_id: str,
    external_id: str = Query(min_length=1, max_length=160),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    board = db.get(PinterestBoard, board_id)
    if board is None:
        raise HTTPException(404, "Board taxonomy record not found")
    board.external_id = external_id
    db.commit()
    return {"id": board.id, "external_id": external_id}


@router.post("/strategy/run", dependencies=[Depends(require_admin)])
def run_strategy(db: Session = Depends(get_db)) -> dict[str, Any]:
    states = detect_winners(db)
    snapshot = create_daily_strategy(db)
    return {"winner_changes": states, "strategy_id": snapshot.id, "summary": snapshot.summary}


@router.post("/onboarding", dependencies=[Depends(require_admin)])
def onboarding(payload: OnboardingInput, db: Session = Depends(get_db)) -> dict[str, Any]:
    safe = payload.model_dump(mode="json")
    row = db.get(AppSetting, "onboarding")
    if row is None:
        row = AppSetting(key="onboarding", value=safe)
        db.add(row)
    else:
        row.value = safe
        row.version += 1
    db.commit()
    return {"configured": True, "version": row.version, "secrets_stored": False}


@router.get("/settings")
def public_settings(settings: Settings = Depends(get_settings)) -> dict[str, Any]:
    return {
        "business_name": settings.business_name,
        "niche": settings.niche,
        "target_country": settings.target_country,
        "currency": settings.currency,
        "demo_mode": settings.demo_mode,
        "dry_run": settings.dry_run,
        "auto_publish": settings.auto_publish,
        "paid_ads_enabled": settings.enable_paid_ads,
        "ai_provider": settings.ai_provider,
        "pinterest_configured": bool(settings.pinterest_access_token and settings.pinterest_board_id),
        "max_posts_per_day": settings.max_posts_per_day,
        "timezone": settings.timezone,
    }


@router.get("/system-health")
def system_health(db: Session = Depends(get_db)) -> dict[str, Any]:
    queue_length = int(
        db.scalar(select(func.count(ContentVariant.id)).where(ContentVariant.status.in_(["approved", "scheduled"])))
        or 0
    )
    failed_jobs = int(db.scalar(select(func.count(JobRun.id)).where(JobRun.status == "failed")) or 0)
    last_sync = db.scalar(
        select(JobRun)
        .where(JobRun.job_name == "product_sync", JobRun.status == "succeeded")
        .order_by(JobRun.completed_at.desc())
        .limit(1)
    )
    last_post = db.scalar(
        select(Publication)
        .where(Publication.status.in_(["published", "dry_run"]))
        .order_by(Publication.published_at.desc())
        .limit(1)
    )
    metrics = overview(db)["today"]
    return {
        "database": "ok",
        "queue_length": queue_length,
        "failed_jobs": failed_jobs,
        "last_successful_product_sync": last_sync.completed_at if last_sync else None,
        "last_successful_post": last_post.published_at if last_post else None,
        "daily_ai_spend": metrics["ai_cost"],
        "daily_ad_spend": metrics["advertising_spend"],
    }


def _oauth_state(settings: Settings) -> str:
    payload = f"{int(time.time())}:{secrets.token_urlsafe(18)}"
    secret = settings.admin_api_key.get_secret_value().encode()
    signature = hmac.new(secret, payload.encode(), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode()).decode()


def _verify_state(state: str, settings: Settings) -> bool:
    try:
        decoded = base64.urlsafe_b64decode(state.encode()).decode()
        timestamp, nonce, signature = decoded.split(":", 2)
        payload = f"{timestamp}:{nonce}"
        expected = hmac.new(
            settings.admin_api_key.get_secret_value().encode(), payload.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected) and time.time() - int(timestamp) < 600
    except (ValueError, UnicodeDecodeError):
        return False


@router.get("/integrations/pinterest/connect", dependencies=[Depends(require_admin)])
def pinterest_connect(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    if not settings.pinterest_app_id:
        raise HTTPException(409, "PINTEREST_APP_ID is not configured")
    params = {
        "client_id": settings.pinterest_app_id,
        "redirect_uri": settings.pinterest_redirect_uri,
        "response_type": "code",
        "scope": "boards:read boards:write pins:read pins:write",
        "state": _oauth_state(settings),
    }
    return {"authorization_url": f"{settings.pinterest_oauth_base}?{urlencode(params)}"}


@router.get("/integrations/pinterest/callback")
def pinterest_callback(
    code: str,
    state: str,
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    if not _verify_state(state, settings):
        raise HTTPException(400, "Invalid or expired OAuth state")
    if not settings.pinterest_app_id or not settings.pinterest_app_secret:
        raise HTTPException(409, "Pinterest app credentials are not configured")
    auth = (settings.pinterest_app_id, settings.pinterest_app_secret.get_secret_value())
    with httpx.Client(timeout=20) as client:
        response = client.post(
            f"{settings.pinterest_api_base}/oauth/token",
            auth=auth,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.pinterest_redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if response.is_error:
        raise HTTPException(502, "Pinterest OAuth exchange failed")
    token = response.json()
    encrypted = encrypt_json(token, settings.admin_api_key.get_secret_value())
    credential = db.get(AppSetting, "credential:pinterest")
    safe_metadata = {
        "encrypted": encrypted,
        "scope": token.get("scope"),
        "expires_in": token.get("expires_in"),
        "connected_at": datetime.now(UTC).isoformat(),
    }
    if credential is None:
        credential = AppSetting(key="credential:pinterest", value=safe_metadata)
        db.add(credential)
    else:
        credential.value = safe_metadata
        credential.version += 1
    db.commit()
    return {
        "connected": True,
        "scope": token.get("scope"),
        "expires_in": token.get("expires_in"),
        "next_step": (
            "Token stored encrypted with the application master secret. Configure a board next; "
            "secret values are never returned to the browser."
        ),
    }


@router.get("/integrations/pinterest/boards", dependencies=[Depends(require_admin)])
def pinterest_boards(settings: Settings = Depends(get_settings), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    try:
        from apps.api.services.publishing import _stored_pinterest_token

        return PinterestPublisher(settings, _stored_pinterest_token(db, settings)).discover_destinations()
    except (ValueError, PermissionError, httpx.HTTPError) as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/go/{slug}", include_in_schema=False)
def track_redirect(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> RedirectResponse:
    link = db.scalar(select(AffiliateLink).where(AffiliateLink.slug == slug))
    if link is None:
        raise HTTPException(404, "Link not found")
    db.add(
        Click(
            affiliate_link_id=link.id,
            content_id=link.content_id,
            platform=request.query_params.get("utm_source", "pinterest"),
            campaign=link.campaign,
            referrer=request.headers.get("referer", "")[:500] or None,
            utm={key: value for key, value in request.query_params.items() if key.startswith("utm_")},
            visitor_hash=anonymize_visitor(request, settings.anonymization_salt.get_secret_value()),
        )
    )
    db.commit()
    response = RedirectResponse(link.affiliate_url, status_code=302)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
