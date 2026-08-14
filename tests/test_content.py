from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

from apps.api.core.config import Settings
from apps.api.db.models import AffiliateLink, ContentVariant, Publication
from apps.api.services.affiliate import ensure_affiliate_link
from apps.api.services.demo import bootstrap_demo
from apps.api.services.publishing import publish_variant
from apps.api.services.quality import validate_content


def demo_settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite:///{tmp_path / 'demo.db'}",
        media_root=tmp_path / "media",
        demo_mode=True,
        dry_run=True,
        admin_api_key="test-admin-token",
    )


def test_demo_pipeline_creates_quality_checked_queue_and_idempotent_publications(db, tmp_path: Path) -> None:
    settings = demo_settings(tmp_path)
    result = bootstrap_demo(db, settings)
    variants = db.scalars(select(ContentVariant)).all()
    assert result["products"] == 6
    assert result["publications"] == 4
    assert len(variants) == 4
    assert all(item.quality_report["passed"] for item in variants)
    assert all(item.media_uri for item in variants)
    assert bootstrap_demo(db, settings)["status"] == "already_initialized"


def test_expired_deal_is_blocked_before_publication(db, tmp_path: Path) -> None:
    settings = demo_settings(tmp_path)
    bootstrap_demo(db, settings)
    variant = db.scalar(select(ContentVariant).limit(1))
    assert variant is not None
    variant.status = "approved"
    variant.idea.deal.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()
    report = validate_content(db, variant, settings)
    assert not report["passed"]
    assert "expired_deal" in report["errors"]
    assert variant.status == "blocked"


def test_missing_disclosure_and_link_are_blocking(db, tmp_path: Path) -> None:
    settings = demo_settings(tmp_path)
    bootstrap_demo(db, settings)
    variant = db.scalar(select(ContentVariant).limit(1))
    assert variant is not None
    variant.caption = "A factual product note without the required statement."
    link = db.scalar(select(AffiliateLink).where(AffiliateLink.content_id == variant.id))
    assert link is not None
    link.content_id = None
    db.commit()
    report = validate_content(db, variant, settings)
    assert {"missing_disclosure", "missing_affiliate_link"}.issubset(report["errors"])


def test_idempotent_publish_restores_terminal_content_state(db, tmp_path: Path) -> None:
    settings = demo_settings(tmp_path)
    bootstrap_demo(db, settings)
    variant = db.scalar(select(ContentVariant).limit(1))
    assert variant is not None
    first_publication_id = db.scalar(select(Publication.id).where(Publication.content_id == variant.id))
    variant.status = "approved"
    db.commit()
    publication = publish_variant(db, variant, ensure_affiliate_link(db, variant, settings), settings)
    assert publication.id == first_publication_id
    assert variant.status == "dry_run"
