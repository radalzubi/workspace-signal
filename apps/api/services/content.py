from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from decimal import Decimal
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import AIUsage, ContentIdea, ContentVariant, Deal
from apps.api.schemas import ContentStrategy

PROHIBITED_CLAIMS = {
    "best ever",
    "guaranteed",
    "lowest price ever",
    "everyone loves this",
    "i've used this",
    "i love this",
}


class ContentStrategyProvider(ABC):
    @abstractmethod
    def generate(self, deal: Deal, disclosure: str) -> tuple[ContentStrategy, dict[str, int]]:
        raise NotImplementedError


class DeterministicContentProvider(ContentStrategyProvider):
    def generate(self, deal: Deal, disclosure: str) -> tuple[ContentStrategy, dict[str, int]]:
        product = deal.product
        stats = deal.price_statistics
        price = f"${Decimal(product.current_price):.2f}"
        discount = Decimal(product.discount_percent).quantize(Decimal("1"))
        strategy = ContentStrategy(
            hook=f"A small-desk upgrade at the current listed price of {price}",
            angle="practical value for compact workspaces",
            title=f"{product.product_name} deal",
            body_copy=(
                f"Based on the listed specifications, {product.product_name} is designed for "
                f"compact workspaces. Current listed price: {price}; listed discount: {discount}%. "
                f"{stats.get('claim_label', 'Price observed by our system')}."
            ),
            cta="Check the current price and availability",
            hashtags=["#DeskSetup", "#HomeOffice", "#SmallSpace", "#DealFinds"],
            voiceover_script=(
                f"Short on desk space? This {product.product_name.lower()} is currently listed at "
                f"{price}. Based on its listed specifications, it may be a practical way to make "
                "a compact setup work harder. Check current price and availability. Affiliate link."
            ),
            visual_sequence=[
                {"seconds": "0-2", "text": "Small desk? Start here."},
                {"seconds": "2-8", "text": product.product_name},
                {"seconds": "8-18", "text": f"Current listed price {price}"},
                {"seconds": "18-25", "text": "Check current price • Affiliate link"},
            ],
            target_audience="people improving compact home-office and desk setups",
            content_category=product.category,
            affiliate_disclosure=disclosure,
            confidence_score=Decimal("86"),
        )
        return strategy, {"input_tokens": 0, "output_tokens": 0}


class OpenAIContentProvider(ContentStrategyProvider):
    """OpenAI Responses API adapter using SDK-native Pydantic structured output."""

    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI

        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key.get_secret_value())  # type: ignore[union-attr]

    def generate(self, deal: Deal, disclosure: str) -> tuple[ContentStrategy, dict[str, int]]:
        product = deal.product
        factual_context = {
            "name": product.product_name,
            "brand": product.brand,
            "category": product.category,
            "description": product.description,
            "current_listed_price": str(product.current_price),
            "list_price": str(product.list_price) if product.list_price is not None else None,
            "currency": product.currency,
            "observed_price_statistics": deal.price_statistics,
            "availability": product.availability,
            "disclosure": disclosure,
        }
        response = self.client.responses.parse(
            model=self.settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "Create factual Pinterest-first affiliate content from only the supplied "
                        "data. Never invent specifications, reviews, personal use, scarcity, or "
                        "price-history claims. Avoid superlatives and include the exact disclosure."
                    ),
                },
                {"role": "user", "content": json.dumps(factual_context, default=str)},
            ],
            text_format=ContentStrategy,
        )
        if response.output_parsed is None:
            raise ValueError("AI provider returned no structured content")
        usage = response.usage
        return response.output_parsed, {
            "input_tokens": usage.input_tokens if usage else 0,
            "output_tokens": usage.output_tokens if usage else 0,
        }


def ai_budget_spend(db: Session, *, days: int) -> Decimal:
    from datetime import timedelta

    since = datetime.now(UTC) - timedelta(days=days)
    value = db.scalar(select(func.coalesce(func.sum(AIUsage.estimated_cost), 0)).where(AIUsage.occurred_at >= since))
    return Decimal(value or 0)


def choose_provider(db: Session, settings: Settings) -> ContentStrategyProvider:
    if settings.ai_provider == "openai" and settings.openai_api_key:
        if (
            ai_budget_spend(db, days=1) >= settings.daily_ai_budget
            or ai_budget_spend(db, days=30) >= settings.monthly_ai_budget
        ):
            return DeterministicContentProvider()
        return OpenAIContentProvider(settings)
    return DeterministicContentProvider()


def strategy_has_unsupported_claim(strategy: ContentStrategy) -> list[str]:
    combined = " ".join(
        [strategy.hook, strategy.title, strategy.body_copy, strategy.cta, strategy.voiceover_script]
    ).lower()
    return sorted(claim for claim in PROHIBITED_CLAIMS if claim in combined)


def content_hash(strategy: ContentStrategy, template_key: str) -> str:
    normalized = "|".join([template_key, strategy.hook.lower(), strategy.title.lower(), strategy.body_copy.lower()])
    return hashlib.sha256(normalized.encode()).hexdigest()


def is_near_duplicate(db: Session, strategy: ContentStrategy, threshold: float = 0.88) -> bool:
    recent = db.scalars(select(ContentVariant.caption).order_by(ContentVariant.created_at.desc()).limit(100)).all()
    candidate = f"{strategy.hook} {strategy.body_copy}".lower()
    return any(SequenceMatcher(None, candidate, existing.lower()).ratio() >= threshold for existing in recent)


def load_templates(
    path: Path = Path("templates/content_templates.json"),
) -> dict[str, dict[str, Any]]:
    decoded: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("Content template root must be an object")
    return {str(key): dict(value) for key, value in decoded.items() if isinstance(value, dict)}


def generate_idea_and_variant(
    db: Session, deal: Deal, settings: Settings, template_key: str = "deal_alert"
) -> ContentVariant:
    provider = choose_provider(db, settings)
    strategy, usage = provider.generate(deal, deal.product.merchant.disclosure_text)
    violations = strategy_has_unsupported_claim(strategy)
    if violations:
        raise ValueError(f"Unsupported claims generated: {', '.join(violations)}")
    if is_near_duplicate(db, strategy):
        template_key = "problem_solution" if template_key != "problem_solution" else "small_space"
        strategy.hook = f"Compact setup idea: {deal.product.product_name}"
    idea = ContentIdea(
        deal_id=deal.id,
        provider="openai" if isinstance(provider, OpenAIContentProvider) else "mock",
        **strategy.model_dump(),
    )
    db.add(idea)
    db.flush()
    caption = (
        f"{strategy.hook}\n\n{strategy.body_copy}\n\n{strategy.cta}\n\n"
        f"{strategy.affiliate_disclosure}\n\n{' '.join(strategy.hashtags)}"
    )
    variant = ContentVariant(
        idea_id=idea.id,
        template_key=template_key,
        platform="pinterest",
        format="image",
        caption=caption,
        content_hash=content_hash(strategy, template_key),
        status="draft",
    )
    db.add(variant)
    input_cost = Decimal(usage["input_tokens"]) / 1_000_000 * settings.openai_input_cost_per_million
    output_cost = Decimal(usage["output_tokens"]) / 1_000_000 * settings.openai_output_cost_per_million
    db.add(
        AIUsage(
            provider=idea.provider,
            model=settings.openai_model if idea.provider == "openai" else "deterministic",
            feature="content_strategy",
            content_id=variant.id,
            input_tokens=usage["input_tokens"],
            output_tokens=usage["output_tokens"],
            estimated_cost=(input_cost + output_cost).quantize(Decimal("0.000001")),
        )
    )
    db.commit()
    return variant
