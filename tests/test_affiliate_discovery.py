from decimal import Decimal

from apps.api.db.models import AffiliateProgram
from apps.api.services.affiliate_discovery import score_affiliate_program


def program(*, rate: str, conversion: str, aov: str, feed: bool, reporting: str) -> AffiliateProgram:
    return AffiliateProgram(
        merchant="Merchant",
        program_name=f"Program {rate}",
        network="test",
        program_url="https://example.com/affiliate",
        status="approved",
        country="US",
        categories=["Monitor Arms"],
        commission_type="percent_sale",
        commission_rate=Decimal(rate),
        cookie_window=30,
        average_order_value=Decimal(aov),
        estimated_conversion_rate=Decimal(conversion),
        product_feed_available=feed,
        api_available=feed,
        deep_linking_available=True,
        media_rights="authorized",
        social_media_allowed=True,
        pinterest_allowed=True,
        paid_search_rules="restricted",
        direct_linking_rules="allowed",
        conversion_reporting="content_id",
        reporting_quality_score=Decimal(reporting),
        payout_threshold=Decimal("25"),
        payment_frequency="monthly",
        application_required=True,
        approval_status="approved",
        merchant_reputation_score=Decimal("85"),
        return_risk_score=Decimal("15"),
        source="https://example.com/official",
        source_kind="official",
        confidence=Decimal("85"),
        notes="",
    )


def test_program_scoring_prefers_expected_value_over_headline_commission() -> None:
    high_rate_poor_conversion = program(rate="0.10", conversion="0.008", aov="35", feed=False, reporting="45")
    lower_rate_strong_conversion = program(rate="0.04", conversion="0.065", aov="90", feed=True, reporting="92")
    high = score_affiliate_program(high_rate_poor_conversion, category="Monitor Arms")
    strong = score_affiliate_program(lower_rate_strong_conversion, category="Monitor Arms")
    assert strong.expected_revenue_per_100_clicks > high.expected_revenue_per_100_clicks
    assert strong.score > high.score


def test_unconfirmed_pinterest_rights_reduce_program_score() -> None:
    candidate = program(rate="0.08", conversion="0.04", aov="70", feed=True, reporting="80")
    confirmed = score_affiliate_program(candidate, category="Monitor Arms")
    candidate.pinterest_allowed = None
    candidate.media_rights = "unknown"
    uncertain = score_affiliate_program(candidate, category="Monitor Arms")
    assert uncertain.score < confirmed.score
    assert "pinterest_permission_unconfirmed" in uncertain.components["risks"]
