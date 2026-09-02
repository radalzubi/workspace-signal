from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import MediaBrand, SocialPublication, StoryClaim, StoryProject, StorySource

OFFICIAL_SOURCE_TYPES = {"official_case", "official_artifact", "court_record", "government_record"}
HIGH_RISK_PATTERNS = (
    r"\bdefinitely killed\b",
    r"\bis the murderer\b",
    r"\bhow to (?:kill|hide a body|evade police)\b",
    r"\bgraphic (?:photo|video|image)\b",
)


def ensure_case_lantern_brand(db: Session, settings: Settings) -> MediaBrand:
    brand = db.scalar(select(MediaBrand).where(MediaBrand.slug == "case-lantern"))
    if brand is None:
        brand = MediaBrand(
            name=settings.case_lantern_brand,
            slug="case-lantern",
            platform="tiktok",
            handle=settings.case_lantern_handle,
            niche="Sourced true crime, disappearances, mysteries, and dark history",
            audience="English-speaking adults interested in concise, evidence-led historical cases",
            bio="True crime, disappearances & dark history. Sources in every caption.",
            brand_config={
                "visual_style": "archival noir; restrained; no gore",
                "voice": "calm documentary narration",
                "profile_image": "generated brass lantern over a case file",
            },
            human_approval_required=True,
        )
        db.add(brand)
        db.flush()
    return brand


def create_pilot_story(db: Session, settings: Settings) -> StoryProject:
    existing = db.scalar(select(StoryProject).where(StoryProject.slug == "db-cooper-vanished"))
    if existing is not None:
        return existing

    brand = ensure_case_lantern_brand(db, settings)
    project = StoryProject(
        brand_id=brand.id,
        title="D.B. Cooper: The Hijacker Who Vanished",
        slug="db-cooper-vanished",
        story_type="historical_unsolved_case",
        status="review",
        hook="A man hijacked a plane, collected $200,000, and vanished into the night.",
        synopsis="A sourced, non-graphic account of the 1971 Northwest Orient Flight 305 hijacking.",
        script=(
            "On November 24, 1971, a man using the name Dan Cooper bought a one-way ticket from "
            "Portland to Seattle. After takeoff, he told a flight attendant that he had a bomb and "
            "demanded four parachutes and two hundred thousand dollars. When the plane landed in "
            "Seattle, the passengers were released in exchange for the ransom and parachutes. The "
            "aircraft took off again with several crew members aboard and a course toward Mexico City. "
            "A little after eight that night, somewhere between Seattle and Reno, Cooper lowered the "
            "rear stairs and jumped into darkness with the money. The pilots landed safely, but Cooper "
            "was never found. The FBI called the investigation NORJAK and pursued leads for decades. "
            "In 1980, a boy found five thousand eight hundred dollars in damaged twenty-dollar bills "
            "whose serial numbers matched the ransom. The discovery proved that some of the money had "
            "reached the ground, but it did not reveal Cooper's fate. The name D.B. Cooper was actually "
            "a press-created mix-up; the ticket was issued to Dan Cooper. In 2016, the FBI redirected "
            "active resources from the case, while still asking that specific physical evidence be "
            "reported. More than fifty years later, no confirmed identity or final explanation has "
            "closed the mystery."
        ),
        caption=(
            "The documented facts behind the D.B. Cooper mystery. Sources: FBI case history and FBI "
            "artifact record. This video summarizes public records; uncertain details are labeled as "
            "unknown. #DBCooper #UnsolvedMystery #DarkHistory #TrueCrime"
        ),
        duration_seconds=82,
        risk_level="low",
        factual_confidence=Decimal("96"),
        visual_plan=[
            {
                "seconds": "0-5",
                "asset": "original animated case-file opener",
                "text": "$200,000. One jump. No confirmed identity.",
            },
            {"seconds": "5-25", "asset": "licensed map animation: Portland to Seattle", "text": "November 24, 1971"},
            {"seconds": "25-50", "asset": "original aircraft silhouette and ransom graphic", "text": "Flight 305"},
            {"seconds": "50-68", "asset": "original riverbank illustration", "text": "$5,800 recovered in 1980"},
            {"seconds": "68-82", "asset": "original evidence-board outro", "text": "What happened after the jump?"},
        ],
        voice_config={"provider": "disabled", "style": "calm_documentary", "human_review": True},
    )
    db.add(project)
    db.flush()

    sources = [
        StorySource(
            project_id=project.id,
            url="https://www.fbi.gov/history/cases-and-criminals/db-cooper-hijacking",
            title="D.B. Cooper Hijacking",
            publisher="Federal Bureau of Investigation",
            source_type="official_case",
            credibility_score=Decimal("100"),
            verified=True,
            notes="Primary official case history; URL checked 2026-08-17.",
        ),
        StorySource(
            project_id=project.id,
            url="https://www.fbi.gov/history/artifacts/d-b-cooper-plane-ticket",
            title="D.B. Cooper Plane Ticket",
            publisher="Federal Bureau of Investigation",
            source_type="official_artifact",
            credibility_score=Decimal("100"),
            verified=True,
            notes="Official artifact record; URL checked 2026-08-17.",
        ),
    ]
    db.add_all(sources)
    db.flush()
    source_ids = [source.id for source in sources]
    claims = [
        "A man using the name Dan Cooper hijacked Northwest Orient Flight 305 on November 24, 1971.",
        "He demanded four parachutes and $200,000 and released passengers in Seattle.",
        "He jumped from the aircraft after 8 p.m. and was never conclusively identified or found.",
        "$5,800 matching the ransom serial numbers was recovered in 1980.",
        "The FBI redirected active investigative resources in 2016.",
    ]
    db.add_all(
        [
            StoryClaim(project_id=project.id, claim_text=claim, source_ids=source_ids, status="supported")
            for claim in claims
        ]
    )
    db.flush()
    project.quality_report = validate_story(db, project, settings)
    db.commit()
    return project


def validate_story(db: Session, project: StoryProject, settings: Settings) -> dict[str, Any]:
    sources = list(db.scalars(select(StorySource).where(StorySource.project_id == project.id)).all())
    claims = list(db.scalars(select(StoryClaim).where(StoryClaim.project_id == project.id)).all())
    source_ids = {source.id for source in sources}
    errors: list[str] = []
    warnings: list[str] = []
    word_count = len(re.findall(r"\b[\w’'-]+\b", project.script))

    if len(sources) < settings.case_lantern_min_sources:
        errors.append(f"At least {settings.case_lantern_min_sources} sources are required.")
    if not any(source.verified and source.source_type in OFFICIAL_SOURCE_TYPES for source in sources):
        errors.append("At least one verified official or primary source is required.")
    if not claims:
        errors.append("At least one structured factual claim is required.")
    unsupported = [claim for claim in claims if claim.status != "supported" or not claim.source_ids]
    invalid_refs = [claim for claim in claims if set(claim.source_ids) - source_ids]
    if unsupported:
        errors.append(f"{len(unsupported)} claim(s) are unsupported or uncited.")
    if invalid_refs:
        errors.append(f"{len(invalid_refs)} claim(s) reference missing sources.")
    if not settings.case_lantern_min_words <= word_count <= settings.case_lantern_max_words:
        errors.append(
            f"Script must be {settings.case_lantern_min_words}-{settings.case_lantern_max_words} words; "
            f"found {word_count}."
        )
    if any(re.search(pattern, project.script, flags=re.IGNORECASE) for pattern in HIGH_RISK_PATTERNS):
        errors.append("Script contains prohibited accusation, graphic-content, or crime-instruction language.")
    if "source" not in project.caption.lower():
        errors.append("Caption must identify its sources.")
    if project.risk_level not in {"low", "medium"}:
        errors.append("High-risk stories cannot enter the automated workflow.")
    if len(project.visual_plan) < 3:
        warnings.append("At least three original or properly licensed visual beats are recommended.")

    supported_ratio = 1.0 if not claims else (len(claims) - len(unsupported) - len(invalid_refs)) / len(claims)
    return {
        "passed": not errors,
        "errors": errors,
        "warnings": warnings,
        "word_count": word_count,
        "estimated_duration_seconds": round(word_count / 2.4),
        "source_count": len(sources),
        "verified_source_count": sum(source.verified for source in sources),
        "supported_claim_ratio": max(0, round(supported_ratio, 3)),
        "human_approval_required": True,
        "public_auto_post_allowed": False,
        "validated_at": datetime.now(UTC).isoformat(),
    }


def story_rows(db: Session) -> list[dict[str, Any]]:
    projects = list(db.scalars(select(StoryProject).order_by(StoryProject.created_at.desc())).all())
    rows: list[dict[str, Any]] = []
    for project in projects:
        sources = list(db.scalars(select(StorySource).where(StorySource.project_id == project.id)).all())
        claims = list(db.scalars(select(StoryClaim).where(StoryClaim.project_id == project.id)).all())
        rows.append(
            {
                "id": project.id,
                "title": project.title,
                "slug": project.slug,
                "status": project.status,
                "story_type": project.story_type,
                "hook": project.hook,
                "synopsis": project.synopsis,
                "script": project.script,
                "caption": project.caption,
                "duration_seconds": project.duration_seconds,
                "risk_level": project.risk_level,
                "factual_confidence": float(project.factual_confidence),
                "quality_report": project.quality_report,
                "visual_plan": project.visual_plan,
                "export_uri": project.export_uri,
                "approved_at": project.approved_at,
                "sources": [
                    {"id": source.id, "url": source.url, "title": source.title, "publisher": source.publisher,
                     "source_type": source.source_type, "verified": source.verified}
                    for source in sources
                ],
                "claims": [
                    {
                        "id": claim.id,
                        "claim_text": claim.claim_text,
                        "source_ids": claim.source_ids,
                        "status": claim.status,
                    }
                    for claim in claims
                ],
            }
        )
    return rows


def apply_story_action(
    db: Session, project: StoryProject, action: str, settings: Settings, reason: str | None = None
) -> StoryProject:
    report = validate_story(db, project, settings)
    project.quality_report = report
    if action == "approve":
        if not report["passed"]:
            raise ValueError("Story cannot be approved until every factual and safety check passes.")
        project.status = "approved"
        project.approved_at = datetime.now(UTC)
    elif action == "reject":
        project.status = "rejected"
        project.quality_report = {**report, "rejection_reason": reason or "Rejected during human review."}
    elif action == "regenerate":
        project.status = "research"
    elif action == "render":
        if project.approved_at is None:
            raise ValueError("Human approval is required before video rendering.")
        from apps.api.services.case_lantern_render import render_story_video

        render_story_video(db, project, settings)
    elif action == "export":
        if project.status not in {"approved", "video_ready", "render_ready"} or project.approved_at is None:
            raise ValueError("Human approval is required before export.")
        project.export_uri = export_story_package(db, project, settings)
        project.status = "render_ready"
        publication = db.scalar(
            select(SocialPublication).where(
                SocialPublication.platform == "tiktok",
                SocialPublication.idempotency_key == f"{project.id}:draft-v1",
            )
        )
        if publication is None:
            db.add(
                SocialPublication(
                    project_id=project.id,
                    platform="tiktok",
                    mode="draft",
                    status="package_ready",
                    idempotency_key=f"{project.id}:draft-v1",
                )
            )
    else:
        raise ValueError("Unsupported story action.")
    db.commit()
    return project


def export_story_package(db: Session, project: StoryProject, settings: Settings) -> str:
    sources = list(db.scalars(select(StorySource).where(StorySource.project_id == project.id)).all())
    output_dir = Path(settings.media_root) / "case-lantern" / project.slug
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "tiktok-draft-package.json"
    payload = {
        "schema_version": "case-lantern-draft-v1",
        "title": project.title,
        "hook": project.hook,
        "script": project.script,
        "caption": project.caption,
        "visual_plan": project.visual_plan,
        "media_uri": project.media_uri,
        "sources": [{"title": source.title, "url": source.url} for source in sources],
        "disclosure": {
            "ai_assisted_visuals": bool(project.media_uri),
            "creator_ai_label_required": bool(project.media_uri),
            "caption_text": "AI-assisted original illustrations and narration." if project.media_uri else None,
        },
        "publishing": {
            "platform": "tiktok",
            "mode": "draft",
            "public_auto_post": False,
            "requires_final_in_app_review": True,
        },
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(output)
