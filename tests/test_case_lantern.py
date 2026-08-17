from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import SocialPublication, StoryClaim
from apps.api.services.case_lantern import apply_story_action, create_pilot_story, story_rows, validate_story


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        admin_api_key="test-admin-token",
        media_root=tmp_path / "media",
        case_lantern_enabled=True,
        case_lantern_human_approval_required=True,
        tiktok_posting_mode="draft",
    )


def test_pilot_is_sourced_and_passes_quality_gate(db: Session, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    project = create_pilot_story(db, settings)
    report = validate_story(db, project, settings)

    assert report["passed"] is True
    assert report["source_count"] == 2
    assert report["verified_source_count"] == 2
    assert report["supported_claim_ratio"] == 1
    assert report["human_approval_required"] is True
    assert report["public_auto_post_allowed"] is False
    assert settings.case_lantern_min_words <= report["word_count"] <= settings.case_lantern_max_words


def test_pilot_creation_is_idempotent(db: Session, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    first = create_pilot_story(db, settings)
    second = create_pilot_story(db, settings)

    assert first.id == second.id
    assert len(story_rows(db)) == 1


def test_unsupported_claim_blocks_approval(db: Session, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    project = create_pilot_story(db, settings)
    claim = db.scalar(select(StoryClaim).where(StoryClaim.project_id == project.id))
    assert claim is not None
    claim.status = "unsupported"
    db.commit()

    with pytest.raises(ValueError, match="cannot be approved"):
        apply_story_action(db, project, "approve", settings)


def test_export_requires_approval_and_creates_draft_package(db: Session, tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    project = create_pilot_story(db, settings)

    with pytest.raises(ValueError, match="Human approval"):
        apply_story_action(db, project, "export", settings)

    apply_story_action(db, project, "approve", settings)
    apply_story_action(db, project, "export", settings)

    assert project.status == "render_ready"
    assert project.export_uri is not None
    package_path = Path(project.export_uri)
    assert package_path.exists()
    package = json.loads(package_path.read_text(encoding="utf-8"))
    assert package["publishing"] == {
        "platform": "tiktok",
        "mode": "draft",
        "public_auto_post": False,
        "requires_final_in_app_review": True,
    }
    publication = db.scalar(select(SocialPublication).where(SocialPublication.project_id == project.id))
    assert publication is not None
    assert publication.status == "package_ready"
    assert publication.mode == "draft"
