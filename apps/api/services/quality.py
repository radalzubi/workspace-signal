from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import AffiliateLink, ContentVariant
from apps.api.services.content import PROHIBITED_CLAIMS


def validate_content(db: Session, variant: ContentVariant, settings: Settings) -> dict[str, object]:
    product = variant.idea.deal.product
    errors: list[str] = []
    warnings: list[str] = []
    combined = variant.caption.lower()
    if not variant.media_uri:
        errors.append("missing_media")
    elif settings.storage_provider == "local":
        path = settings.media_root.resolve() / Path(variant.media_uri).name
        if not path.exists() or path.stat().st_size < 1_000:
            errors.append("rendering_error")
    if any(claim in combined for claim in PROHIBITED_CLAIMS):
        errors.append("unsupported_claim")
    if "affiliate" not in combined or "commission" not in combined:
        errors.append("missing_disclosure")
    link = db.scalar(select(AffiliateLink).where(AffiliateLink.content_id == variant.id))
    if link is None:
        errors.append("missing_affiliate_link")
    elif urlparse(link.affiliate_url).scheme not in {"http", "https"}:
        errors.append("broken_affiliate_url")
    if product.availability != "in_stock":
        errors.append("unavailable_product")
    observed_at = product.last_observed_at
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=UTC)
    age = datetime.now(UTC) - observed_at
    if age > timedelta(hours=settings.deal_max_age_hours):
        errors.append("outdated_price")
    expires_at = variant.idea.deal.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= datetime.now(UTC):
        errors.append("expired_deal")
    if len(variant.caption) > 800:
        errors.append("caption_too_long")
    if len(variant.caption) > 700:
        warnings.append("caption_near_platform_limit")
    report: dict[str, object] = {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "checked_at": datetime.now(UTC).isoformat(),
    }
    variant.quality_report = report
    if errors and variant.status not in {"published", "rejected"}:
        variant.status = "blocked"
    db.commit()
    return report
