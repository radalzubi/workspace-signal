from pathlib import Path

from apps.api.core.config import Settings
from apps.api.services.analytics import overview, weekly_business_report
from apps.api.services.demo import bootstrap_demo


def test_analytics_reconcile_seeded_funnel(db, tmp_path: Path) -> None:
    settings = Settings(media_root=tmp_path / "media", demo_mode=True, dry_run=True)
    bootstrap_demo(db, settings)
    lifetime = overview(db)["lifetime"]
    assert lifetime["impressions"] == 3610
    assert lifetime["clicks"] == 97
    assert lifetime["conversions"] == 3
    assert lifetime["affiliate_revenue"] == 11.94
    assert lifetime["gross_profit"] > 0


def test_weekly_report_is_evidence_based(db, tmp_path: Path) -> None:
    settings = Settings(media_root=tmp_path / "media", demo_mode=True, dry_run=True)
    bootstrap_demo(db, settings)
    report = weekly_business_report(db)
    assert report["period"] == "last_7_days"
    assert report["profit"] == report["evidence"]["gross_profit"]
    assert report["recommended_changes"]
