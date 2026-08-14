from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.db.models import AffiliateProgram, AffiliateProgramScore, Merchant
from apps.api.schemas import AffiliateProgramInput


@dataclass(frozen=True)
class ProgramEvaluation:
    score: Decimal
    expected_revenue_per_100_clicks: Decimal
    components: dict[str, float | str | list[str]]
    confidence: Decimal


class AffiliateProgramProvider(ABC):
    """Discovery adapters return research records; they never apply to programs."""

    @abstractmethod
    def discover(self) -> list[AffiliateProgramInput]:
        raise NotImplementedError


class JSONAffiliateProgramProvider(AffiliateProgramProvider):
    def __init__(self, path: Path) -> None:
        self.path = path.resolve(strict=True)

    def discover(self) -> list[AffiliateProgramInput]:
        if self.path.stat().st_size > 5_000_000:
            raise ValueError("Affiliate program file exceeds 5 MB")
        decoded: object = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(decoded, dict) or not isinstance(decoded.get("programs"), list):
            raise ValueError("Affiliate directory must contain a programs list")
        return TypeAdapter(list[AffiliateProgramInput]).validate_python(decoded["programs"])


def score_affiliate_program(program: AffiliateProgram, *, category: str | None = None) -> ProgramEvaluation:
    commission_rate = Decimal(program.commission_rate)
    conversion_rate = Decimal(program.estimated_conversion_rate or Decimal("0.02"))
    order_value = Decimal(program.average_order_value or Decimal("50"))
    expected_revenue = (Decimal("100") * conversion_rate * order_value * commission_rate).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
    commission = min(Decimal("100"), commission_rate * Decimal("1000"))
    conversion = min(Decimal("100"), conversion_rate / Decimal("0.08") * Decimal("100"))
    aov = min(Decimal("100"), order_value / Decimal("150") * Decimal("100"))
    feed_quality = Decimal(
        20
        + (35 if program.product_feed_available else 0)
        + (25 if program.api_available else 0)
        + (20 if program.deep_linking_available else 0)
    )
    content_fit = Decimal("90") if category and category in (program.categories or []) else Decimal("58")
    pinterest = (
        Decimal("100")
        if program.pinterest_allowed is True
        else Decimal("0")
        if program.pinterest_allowed is False
        else Decimal("35")
    )
    reporting = Decimal(program.reporting_quality_score)
    reputation = Decimal(program.merchant_reputation_score)
    cookie = min(Decimal("100"), Decimal(program.cookie_window or 0) / Decimal("45") * Decimal("100"))
    weighted = (
        commission * Decimal("0.16")
        + conversion * Decimal("0.20")
        + aov * Decimal("0.08")
        + feed_quality * Decimal("0.13")
        + content_fit * Decimal("0.12")
        + pinterest * Decimal("0.12")
        + reporting * Decimal("0.08")
        + reputation * Decimal("0.07")
        + cookie * Decimal("0.04")
    )
    risks: list[str] = []
    risk_penalty = Decimal(program.return_risk_score) * Decimal("0.10")
    if program.pinterest_allowed is None:
        risks.append("pinterest_permission_unconfirmed")
        risk_penalty += Decimal("8")
    elif not program.pinterest_allowed:
        risks.append("pinterest_not_allowed")
        risk_penalty += Decimal("40")
    if program.media_rights in {"unknown", "restricted"}:
        risks.append("media_rights_unconfirmed")
        risk_penalty += Decimal("7")
    if program.approval_status != "approved":
        risks.append("program_not_approved")
        risk_penalty += Decimal("6")
    if program.status in {"paused", "disabled", "rejected"}:
        risks.append("program_unavailable")
        risk_penalty += Decimal("50")
    score = max(Decimal("0"), min(Decimal("100"), weighted - risk_penalty)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    completeness = sum(
        [
            program.cookie_window is not None,
            program.average_order_value is not None,
            program.estimated_conversion_rate is not None,
            program.pinterest_allowed is not None,
            program.media_rights != "unknown",
            program.conversion_reporting != "unknown",
            program.terms_last_checked is not None or program.source_kind == "demo",
        ]
    )
    confidence = min(
        Decimal("100"),
        Decimal(program.confidence) * Decimal("0.7") + Decimal(completeness) / Decimal("7") * Decimal("30"),
    ).quantize(Decimal("0.01"))
    return ProgramEvaluation(
        score=score,
        expected_revenue_per_100_clicks=expected_revenue,
        confidence=confidence,
        components={
            "commission_value": float(commission),
            "conversion_probability": float(conversion),
            "average_order_value": float(aov),
            "feed_api_quality": float(feed_quality),
            "content_fit": float(content_fit),
            "pinterest_suitability": float(pinterest),
            "reporting_quality": float(reporting),
            "merchant_reputation": float(reputation),
            "cookie_window": float(cookie),
            "risk_penalty": float(risk_penalty),
            "risks": risks,
            "summary": (
                "Expected value combines commission, conversion, order value, catalog quality, policy fit and risk."
            ),
        },
    )


def persist_affiliate_programs(db: Session, programs: list[AffiliateProgramInput]) -> list[AffiliateProgram]:
    saved: list[AffiliateProgram] = []
    for item in programs:
        row = db.scalar(
            select(AffiliateProgram).where(
                AffiliateProgram.network == item.network,
                AffiliateProgram.program_name == item.program_name,
                AffiliateProgram.country == item.country,
            )
        )
        merchant = db.scalar(select(Merchant).where(Merchant.name == item.merchant))
        values = item.model_dump(mode="python")
        values["program_url"] = str(values["program_url"])
        values["merchant_id"] = merchant.id if merchant else None
        if row is None:
            row = AffiliateProgram(**values)
            db.add(row)
            db.flush()
        else:
            for key, value in values.items():
                setattr(row, key, value)
        evaluation = score_affiliate_program(row)
        prior = db.scalar(
            select(AffiliateProgramScore)
            .where(AffiliateProgramScore.program_id == row.id)
            .order_by(AffiliateProgramScore.calculated_at.desc())
            .limit(1)
        )
        if prior is None or prior.components != evaluation.components:
            db.add(
                AffiliateProgramScore(
                    program_id=row.id,
                    attractiveness_score=evaluation.score,
                    expected_revenue_per_100_clicks=evaluation.expected_revenue_per_100_clicks,
                    components=evaluation.components,
                    confidence=evaluation.confidence,
                )
            )
        saved.append(row)
    db.commit()
    return saved


def discover_from_provider(db: Session, provider: AffiliateProgramProvider) -> list[AffiliateProgram]:
    return persist_affiliate_programs(db, provider.discover())


def rescore_affiliate_programs(db: Session) -> int:
    count = 0
    for program in db.scalars(select(AffiliateProgram)).all():
        evaluation = score_affiliate_program(program)
        db.add(
            AffiliateProgramScore(
                program_id=program.id,
                attractiveness_score=evaluation.score,
                expected_revenue_per_100_clicks=evaluation.expected_revenue_per_100_clicks,
                components=evaluation.components,
                confidence=evaluation.confidence,
            )
        )
        count += 1
    db.commit()
    return count


def affiliate_program_rows(db: Session) -> list[dict[str, Any]]:
    programs = db.scalars(select(AffiliateProgram).order_by(AffiliateProgram.created_at.desc())).all()
    result: list[dict[str, Any]] = []
    for program in programs:
        score = db.scalar(
            select(AffiliateProgramScore)
            .where(AffiliateProgramScore.program_id == program.id)
            .order_by(AffiliateProgramScore.calculated_at.desc())
            .limit(1)
        )
        result.append(
            {
                "id": program.id,
                "merchant": program.merchant,
                "program_name": program.program_name,
                "network": program.network,
                "program_url": program.program_url,
                "status": program.status,
                "approval_status": program.approval_status,
                "country": program.country,
                "categories": program.categories,
                "commission_type": program.commission_type,
                "commission_rate": float(program.commission_rate),
                "cookie_window": program.cookie_window,
                "average_order_value": float(program.average_order_value)
                if program.average_order_value is not None
                else None,
                "product_feed_available": program.product_feed_available,
                "api_available": program.api_available,
                "deep_linking_available": program.deep_linking_available,
                "media_rights": program.media_rights,
                "social_media_allowed": program.social_media_allowed,
                "pinterest_allowed": program.pinterest_allowed,
                "conversion_reporting": program.conversion_reporting,
                "terms_last_checked": program.terms_last_checked,
                "source": program.source,
                "source_kind": program.source_kind,
                "notes": program.notes,
                "attractiveness_score": float(score.attractiveness_score) if score else None,
                "expected_revenue_per_100_clicks": float(score.expected_revenue_per_100_clicks) if score else None,
                "score_confidence": float(score.confidence) if score else 0,
                "score_components": score.components if score else {},
            }
        )
    return result


def discovery_source_catalog() -> list[dict[str, Any]]:
    return [
        {
            "provider": "json_csv",
            "implemented": True,
            "credentials_required": False,
            "capabilities": ["research_import", "terms_metadata", "program_scoring"],
        },
        {
            "provider": "impact_partner_api",
            "implemented": False,
            "credentials_required": True,
            "capabilities": ["available_catalog_search", "actions", "reports"],
            "official_docs": "https://integrations.impact.com/impact-publisher",
        },
        {
            "provider": "awin_publisher_api",
            "implemented": False,
            "credentials_required": True,
            "capabilities": ["program_information", "product_feeds", "transactions"],
            "official_docs": "https://help.awin.com/apidocs/for-publishers",
        },
        {
            "provider": "cj_publisher_api",
            "implemented": False,
            "credentials_required": True,
            "capabilities": ["program_terms", "product_feed_search", "commission_details"],
            "official_docs": "https://docs.cj.com/docs/finding-your-path",
        },
        {
            "provider": "amazon_creators_api",
            "implemented": False,
            "credentials_required": True,
            "capabilities": ["authorized_product_content", "product_recommendations"],
            "eligibility_note": (
                "Marketplace enrollment, qualifying-sales threshold and API registration are externally enforced."
            ),
            "official_docs": "https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction",
        },
    ]
