from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select

from apps.api.core.config import get_settings
from apps.api.db.models import StoryClaim, StoryProject, StorySource
from apps.api.db.session import SessionLocal
from apps.api.services.case_lantern import ensure_case_lantern_brand, validate_story

SLUG = "uss-cyclops-1918-disappearance"


def main() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        existing = db.scalar(select(StoryProject).where(StoryProject.slug == SLUG))
        if existing is not None:
            print({"story_id": existing.id, "status": existing.status, "created": False})
            return

        brand = ensure_case_lantern_brand(db, settings)
        project = StoryProject(
            brand_id=brand.id,
            title="USS Cyclops: 306 People and a Ship Vanished",
            slug=SLUG,
            story_type="historical_unsolved_case",
            status="review",
            hook="A U.S. Navy ship left Barbados in 1918—and neither the vessel nor its 306 people returned.",
            synopsis=(
                "A restrained, source-grounded account of the unexplained 1918 disappearance of USS Cyclops."
            ),
            script=(
                "On March 4, 1918, USS Cyclops left Barbados for Baltimore carrying manganese ore and "
                "306 people. The Navy collier never arrived. No distress call was recorded, and no confirmed "
                "wreckage has been found. Cyclops had departed Rio de Janeiro on February 16, stopping at "
                "Barbados on March 3 and 4. Its official ship history calls the loss one of the sea’s unsolved "
                "mysteries. Because the disappearance happened during World War One, enemy action was suspected. "
                "Later reviews of German records, however, produced no evidence that a submarine or raider attacked "
                "the vessel. The ship’s load and condition have fueled more grounded theories. National Archives "
                "historians note reports that Cyclops was overloaded and had a cracked engine cylinder before "
                "continuing toward the United States. Navy historians have discussed storms, structural failure, "
                "and the difficulties of carrying dense manganese ore, but none is a confirmed cause. The Bermuda "
                "Triangle label came later and does not resolve the evidence. What remains documented is narrower: "
                "a Navy ship left Barbados, 306 people vanished with it, no distress signal identified the crisis, "
                "and more than a century later the wreck and cause remain unknown. Without a wreck site, every "
                "explanation remains a theory."
            ),
            caption=(
                "USS Cyclops vanished in 1918 with 306 people aboard. Sources: U.S. Naval History and Heritage "
                "Command ship history and H-Gram 016; U.S. National Archives. No cause has been confirmed. "
                "#USSCyclops #MaritimeMystery #DarkHistory #UnsolvedMystery"
            ),
            duration_seconds=82,
            risk_level="low",
            factual_confidence=Decimal("95"),
            visual_plan=[
                {
                    "seconds": "0-6",
                    "asset": "original case-file opener with ship silhouette",
                    "text": "306 people. No distress call. No wreck.",
                },
                {
                    "seconds": "6-28",
                    "asset": "original route-map animation: Brazil, Barbados, Baltimore",
                    "text": "Last seen: March 4, 1918",
                },
                {
                    "seconds": "28-52",
                    "asset": "original manganese-cargo and ship schematic",
                    "text": "Enemy action was suspected—but never supported",
                },
                {
                    "seconds": "52-70",
                    "asset": "original storm-sea illustration",
                    "text": "Storm, structural failure, overload: theories only",
                },
                {
                    "seconds": "70-82",
                    "asset": "original empty-ocean evidence-board outro",
                    "text": "The cause remains unknown",
                },
            ],
            voice_config={"provider": "disabled", "style": "calm_documentary", "human_review": True},
        )
        db.add(project)
        db.flush()

        navy_history = StorySource(
            project_id=project.id,
            url=(
                "https://www.history.navy.mil/research/histories/ship-histories/danfs/c/"
                "cyclops-fuel-ship-no-4-ii1.html"
            ),
            title="Cyclops II (Fuel Ship No. 4)",
            publisher="U.S. Naval History and Heritage Command",
            source_type="official_case",
            credibility_score=Decimal("100"),
            verified=True,
            notes="Official Navy ship history; checked 2026-09-02.",
        )
        navy_analysis = StorySource(
            project_id=project.id,
            url=(
                "https://www.history.navy.mil/about-us/leadership/director/directors-corner/"
                "h-grams/h-gram-016.html"
            ),
            title="H-Gram 016: The Disappearance of USS Cyclops",
            publisher="U.S. Naval History and Heritage Command",
            source_type="official_case",
            credibility_score=Decimal("100"),
            verified=True,
            notes="Official Navy historical analysis; checked 2026-09-02.",
        )
        archives = StorySource(
            project_id=project.id,
            url=(
                "https://unwritten-record.blogs.archives.gov/2021/10/28/"
                "her-loss-remains-unknown-the-mysterious-disappearance-of-the-uss-cyclops-ac-4/"
            ),
            title="The Mysterious Disappearance of the USS Cyclops (AC-4)",
            publisher="U.S. National Archives",
            source_type="government_record",
            credibility_score=Decimal("95"),
            verified=True,
            notes="National Archives history grounded in agency records; checked 2026-09-02.",
        )
        db.add_all([navy_history, navy_analysis, archives])
        db.flush()

        db.add_all(
            [
                StoryClaim(
                    project_id=project.id,
                    claim_text=(
                        "USS Cyclops departed Barbados in March 1918 for Baltimore and was never heard from again."
                    ),
                    source_ids=[navy_history.id, navy_analysis.id],
                    status="supported",
                ),
                StoryClaim(
                    project_id=project.id,
                    claim_text="The ship carried manganese ore and 306 people.",
                    source_ids=[navy_analysis.id],
                    status="supported",
                ),
                StoryClaim(
                    project_id=project.id,
                    claim_text="No distress call or confirmed trace of the ship was found.",
                    source_ids=[navy_analysis.id],
                    status="supported",
                ),
                StoryClaim(
                    project_id=project.id,
                    claim_text="Postwar records provided no evidence that German forces caused the loss.",
                    source_ids=[navy_analysis.id],
                    status="supported",
                ),
                StoryClaim(
                    project_id=project.id,
                    claim_text="Reports described the ship as overloaded and having a cracked engine cylinder.",
                    source_ids=[archives.id],
                    status="supported",
                ),
                StoryClaim(
                    project_id=project.id,
                    claim_text="The wreck and cause of the disappearance remain unknown.",
                    source_ids=[navy_history.id, archives.id],
                    status="supported",
                ),
            ]
        )
        db.flush()
        project.quality_report = validate_story(db, project, settings)
        db.commit()
        print(
            {
                "story_id": project.id,
                "status": project.status,
                "created": True,
                "quality_passed": project.quality_report["passed"],
                "word_count": project.quality_report["word_count"],
                "source_count": project.quality_report["source_count"],
            }
        )


if __name__ == "__main__":
    main()
