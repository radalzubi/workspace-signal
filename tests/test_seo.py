from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import select

from apps.api.core.config import Settings
from apps.api.db.models import ContentBrief, Keyword, Product
from apps.api.services.analytics import keyword_performance_report, seo_commercial_analytics
from apps.api.services.demo import bootstrap_demo
from apps.api.services.seo import (
    classify_search_intent,
    detect_keyword_stuffing,
    generate_long_tail_keywords,
    keyword_experiment_result,
    normalize_keyword,
    score_pin_title,
)


@pytest.mark.parametrize(
    ("term", "intent"),
    [
        ("desk setup ideas", "inspiration"),
        ("best monitor arm small desk", "comparison"),
        ("monitor arm deal", "deal"),
        ("desk accessories under $50", "budget"),
        ("how to organize small desk", "problem_solution"),
        ("buy compact laptop stand", "purchase_intent"),
    ],
)
def test_search_intent_classification(term: str, intent: str) -> None:
    assert classify_search_intent(term) == intent


def test_keyword_normalization_is_stable() -> None:
    assert normalize_keyword("  Best—Monitor Arm & Small Desk!! ") == "best monitor arm and small desk"
    assert normalize_keyword("DESK   Accessories under $50") == "desk accessories under $50"


def test_long_tail_generation_stays_product_relevant() -> None:
    product = Product(
        provider="test",
        provider_product_id="arm",
        product_name="Compact Monitor Arm",
        category="Monitor Arms",
        description="VESA-compatible arm based on listed specifications.",
        current_price=Decimal("59"),
        list_price=Decimal("89"),
        currency="USD",
        discount_percent=Decimal("33"),
        canonical_product_url="https://example.com/arm",
        availability="in_stock",
        expected_commission_rate=Decimal("0.05"),
        merchant_id="merchant",
    )
    terms = generate_long_tail_keywords(product, "small desk lacks usable surface space")
    assert "monitor arm for small desk" in terms
    assert all("monitor" in term or "arm" in term for term in terms)
    assert len(terms) == len(set(terms))


def test_title_scoring_blocks_stuffing_and_unverified_numbers() -> None:
    bad = "BEST CHEAP DESK DEAL SALE BUY BUY NOW 2026!!!"
    assert {"excessive_uppercase", "commercial_term_stacking"}.issubset(detect_keyword_stuffing(bad))
    evaluation = score_pin_title(
        "5 Best Monitor Arms for a Small Desk",
        primary_keyword="best monitor arm for small desk",
        intent="comparison",
        verified_numbers=set(),
    )
    assert evaluation.factors["factual_accuracy"] == 0
    assert evaluation.score < 90


def test_demo_builds_grounded_briefs_board_relevance_and_keyword_profit(db, tmp_path: Path) -> None:
    settings = Settings(media_root=tmp_path / "media", demo_mode=True, dry_run=True)
    bootstrap_demo(db, settings)
    briefs = db.scalars(select(ContentBrief)).all()
    assert len(briefs) == 4
    for brief in briefs:
        product = db.get(Product, brief.product_id)
        keyword = db.get(Keyword, brief.primary_keyword_id)
        assert product is not None and keyword is not None
        assert product.product_name == brief.verified_product_facts["name"]
        assert product.description == brief.verified_product_facts["description"]
        assert len(brief.selected_title) <= 100
        assert brief.search_intent == keyword.intent
        assert brief.board.name
        assert "affiliate" in brief.disclosure.lower()
        assert not {"rating", "reviews"}.intersection(brief.verified_product_facts)
    performance = keyword_performance_report(db)
    assert any(row["impressions"] > 0 for row in performance)
    assert any(row["conversions"] > 0 and row["profit"] > 0 for row in performance)
    analytics = seo_commercial_analytics(db)
    assert analytics["price_bands"]
    assert analytics["discount_bands"]
    assert {row["label"] for row in analytics["content_types"]} == {"evergreen", "deal"}


def test_keyword_experiments_require_meaningful_samples() -> None:
    small = [
        {"label": "a", "impressions": 499, "clicks": 19, "conversions": 2, "profit": Decimal("20")},
        {"label": "b", "impressions": 700, "clicks": 30, "conversions": 4, "profit": Decimal("15")},
    ]
    assert (
        keyword_experiment_result(
            small,
            minimum_impressions=500,
            minimum_clicks=20,
            minimum_conversions=3,
        )["status"]
        == "insufficient_sample"
    )
    ready = [
        {"label": "a", "impressions": 600, "clicks": 25, "conversions": 3, "profit": Decimal("20")},
        {"label": "b", "impressions": 700, "clicks": 30, "conversions": 4, "profit": Decimal("15")},
    ]
    result = keyword_experiment_result(
        ready,
        minimum_impressions=500,
        minimum_clicks=20,
        minimum_conversions=3,
    )
    assert result == {"status": "decision_ready", "winner": "a", "optimization_metric": "profit"}
