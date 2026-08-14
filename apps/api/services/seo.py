from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import (
    BoardKeyword,
    ContentBrief,
    ContentIdea,
    ContentKeyword,
    ContentVariant,
    Deal,
    Keyword,
    KeywordCluster,
    KeywordClusterMember,
    PinterestBoard,
    Product,
    ProductKeyword,
    ProductProblem,
)
from apps.api.schemas import ContentBriefPlan

INTENTS = {
    "informational",
    "inspiration",
    "problem_solution",
    "product_discovery",
    "comparison",
    "budget",
    "deal",
    "purchase_intent",
    "brand_specific",
}
STOPWORDS = {"a", "an", "and", "at", "for", "in", "of", "on", "the", "to", "with"}
COMMERCIAL_WORDS = {"best", "buy", "cheap", "deal", "discount", "sale", "shop", "top"}


@dataclass(frozen=True)
class TitleEvaluation:
    title: str
    score: Decimal
    factors: dict[str, float | bool | list[str]]


def load_seo_taxonomy(path: Path) -> dict[str, Any]:
    decoded: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(decoded, dict) or not isinstance(decoded.get("boards"), list):
        raise ValueError("SEO taxonomy must contain a boards list")
    return decoded


def normalize_keyword(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower().replace("&", " and ")
    normalized = re.sub(r"[^a-z0-9$]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _tokens(value: str) -> list[str]:
    return [token for token in normalize_keyword(value).split() if token not in STOPWORDS]


def classify_search_intent(keyword: str, *, known_brands: set[str] | None = None) -> str:
    value = normalize_keyword(keyword)
    tokens = set(value.split())
    brands = {normalize_keyword(item) for item in known_brands or set()}
    if any(brand and brand in value for brand in brands):
        return "brand_specific"
    if tokens & {"deal", "deals", "discount", "sale", "coupon"} or "price drop" in value:
        return "deal"
    if tokens & {"under", "budget", "affordable", "cheap"} or re.search(r"under \$?\d+", value):
        return "budget"
    if tokens & {"best", "versus", "vs", "compare", "comparison", "review"}:
        return "comparison"
    if tokens & {"buy", "shop", "purchase"} or "for sale" in value:
        return "purchase_intent"
    if value.startswith("how ") or tokens & {"organize", "fix", "reduce", "free"}:
        return "problem_solution"
    if tokens & {"ideas", "inspiration", "aesthetic"} or value.endswith("setup"):
        return "inspiration"
    if " for " in f" {value} " or tokens & {"accessories", "products", "upgrades"}:
        return "product_discovery"
    return "informational"


def score_keyword(
    keyword: str,
    *,
    niche: str,
    product: Product | None = None,
    trend_score: Decimal = Decimal("50"),
    competition_estimate: Decimal | None = None,
) -> dict[str, Decimal | str]:
    normalized = normalize_keyword(keyword)
    intent = classify_search_intent(keyword, known_brands={product.brand} if product and product.brand else None)
    intent_base = {
        "informational": (25, 15, 5),
        "inspiration": (35, 18, 5),
        "problem_solution": (60, 45, 8),
        "product_discovery": (68, 58, 10),
        "comparison": (82, 78, 12),
        "budget": (83, 74, 62),
        "deal": (88, 82, 95),
        "purchase_intent": (95, 96, 25),
        "brand_specific": (90, 88, 20),
    }[intent]
    keyword_tokens = set(_tokens(normalized))
    niche_tokens = set(_tokens(niche))
    product_tokens = set(_tokens(f"{product.product_name} {product.category}")) if product else set()
    reference = niche_tokens | product_tokens
    overlap = len(keyword_tokens & reference) / max(len(keyword_tokens), 1)
    specificity = min(max(len(keyword_tokens) - 1, 0) * 7, 28)
    relevance = Decimal(str(min(100, 42 + overlap * 45 + specificity))).quantize(Decimal("0.01"))
    competition = competition_estimate or Decimal(
        str(max(18, 76 - specificity + (8 if intent == "inspiration" else 0)))
    )
    return {
        "intent": intent,
        "commercial_intent_score": Decimal(intent_base[0]),
        "purchase_intent_score": Decimal(intent_base[1]),
        "deal_intent_score": Decimal(intent_base[2]),
        "search_relevance": relevance,
        "trend_score": max(Decimal("0"), min(trend_score, Decimal("100"))),
        "competition_estimate": max(Decimal("0"), min(competition, Decimal("100"))),
        "confidence": Decimal("58") if product else Decimal("50"),
    }


def upsert_keyword(
    db: Session,
    keyword: str,
    *,
    niche: str,
    category: str | None = None,
    product: Product | None = None,
    source: str = "deterministic_hypothesis",
    trend_score: Decimal = Decimal("50"),
) -> Keyword:
    normalized = normalize_keyword(keyword)
    row = db.scalar(select(Keyword).where(Keyword.normalized_keyword == normalized, Keyword.niche == niche))
    scored = score_keyword(keyword, niche=niche, product=product, trend_score=trend_score)
    values = {
        "keyword": keyword.strip(),
        "category": category,
        "intent": str(scored["intent"]),
        "commercial_intent_score": Decimal(scored["commercial_intent_score"]),
        "purchase_intent_score": Decimal(scored["purchase_intent_score"]),
        "deal_intent_score": Decimal(scored["deal_intent_score"]),
        "search_relevance": Decimal(scored["search_relevance"]),
        "trend_score": Decimal(scored["trend_score"]),
        "competition_estimate": Decimal(scored["competition_estimate"]),
        "source": source,
        "confidence": Decimal(scored["confidence"]),
    }
    if row is None:
        row = Keyword(normalized_keyword=normalized, niche=niche, **values)
        db.add(row)
        db.flush()
    else:
        for key, value in values.items():
            setattr(row, key, value)
    return row


def _category_base(category: str) -> str:
    aliases = {
        "Monitor Arms": "monitor arm",
        "Laptop Stands": "laptop stand",
        "Cable Management": "cable management",
        "Organization": "desk storage",
        "Accessories": "desk accessory",
        "Lighting": "desk lamp",
    }
    return aliases.get(category, normalize_keyword(category))


def generate_long_tail_keywords(product: Product, problem: str | None = None) -> list[str]:
    base = _category_base(product.category)
    current = Decimal(product.current_price)
    ceiling = 25 if current <= 25 else 50 if current <= 50 else 100 if current <= 100 else 250
    candidates = [
        f"{base} for small desk",
        f"best {base} for small desk",
        f"space saving {base} for small desk",
        f"{base} under ${ceiling}",
        f"{base} for small home office",
        f"{base} deal",
    ]
    if problem:
        problem_tokens = " ".join(_tokens(problem)[:5])
        candidates.append(f"{base} for {problem_tokens}")
    valid: list[str] = []
    base_tokens = set(_tokens(base))
    for candidate in candidates:
        normalized = normalize_keyword(candidate)
        tokens = normalized.split()
        if not 2 <= len(tokens) <= 10 or len(normalized) > 90:
            continue
        if not base_tokens.intersection(tokens) or any(a == b for a, b in zip(tokens, tokens[1:], strict=False)):
            continue
        if normalized not in valid:
            valid.append(normalized)
    return valid


def _cluster_slug(value: str) -> str:
    return normalize_keyword(value).replace(" ", "-")


def seed_seo_taxonomy(db: Session, settings: Settings) -> dict[str, int]:
    config = load_seo_taxonomy(settings.seo_taxonomy_path)
    niche = settings.niche
    products = db.scalars(select(Product)).all()
    keywords: dict[str, Keyword] = {}
    configured = [str(item) for item in config.get("seed_keywords", [])]
    for term in configured:
        row = upsert_keyword(db, term, niche=niche, source="curated_demo_configuration")
        keywords[row.normalized_keyword] = row
    problem_config = config.get("problems", {})
    if not isinstance(problem_config, dict):
        problem_config = {}
    for product in products:
        details = problem_config.get(product.category, {})
        problem = str(details.get("problem", "workspace has limited usable space")) if isinstance(details, dict) else ""
        solution = (
            str(details.get("solution", product.description)) if isinstance(details, dict) else product.description
        )
        normalized_problem = normalize_keyword(problem)
        if not db.scalar(
            select(ProductProblem).where(
                ProductProblem.product_id == product.id,
                ProductProblem.normalized_problem == normalized_problem,
            )
        ):
            db.add(
                ProductProblem(
                    product_id=product.id,
                    problem=problem,
                    normalized_problem=normalized_problem,
                    solution=solution,
                    relevance_score=Decimal("88"),
                    confidence=Decimal("75"),
                )
            )
        terms = generate_long_tail_keywords(product, problem)
        for term in terms:
            row = upsert_keyword(db, term, niche=niche, category=product.category, product=product)
            keywords[row.normalized_keyword] = row
        for row in keywords.values():
            scored = score_keyword(row.keyword, niche=niche, product=product, trend_score=Decimal(row.trend_score))
            match = Decimal(scored["search_relevance"])
            category_tokens = set(_tokens(product.category))
            if category_tokens.intersection(_tokens(row.keyword)) or row.category == product.category:
                match = min(Decimal("100"), match + Decimal("18"))
            if match < 55:
                continue
            association = db.scalar(
                select(ProductKeyword).where(
                    ProductKeyword.product_id == product.id,
                    ProductKeyword.keyword_id == row.id,
                )
            )
            if association is None:
                db.add(
                    ProductKeyword(
                        product_id=product.id,
                        keyword_id=row.id,
                        relevance=match,
                        product_match=match,
                    )
                )
    db.flush()
    cluster_specs = [
        ("Small Desk Setup", "topic", "inspiration", None),
        ("Budget Desk Setup", "commercial", "budget", None),
        ("Workspace Deals", "commercial", "deal", None),
        *((category, "product", "product_discovery", category) for category in config.get("categories", {})),
    ]
    clusters: list[KeywordCluster] = []
    all_keywords = db.scalars(select(Keyword).where(Keyword.niche == niche)).all()
    for name, cluster_type, intent, category in cluster_specs:
        slug = _cluster_slug(name)
        cluster = db.scalar(select(KeywordCluster).where(KeywordCluster.slug == slug, KeywordCluster.niche == niche))
        matching = [
            row
            for row in all_keywords
            if (category and (row.category == category or set(_tokens(category)) & set(_tokens(row.keyword))))
            or (not category and row.intent == intent)
        ]
        if not matching and name == "Small Desk Setup":
            matching = [row for row in all_keywords if "desk" in row.normalized_keyword][:8]
        primary = max(
            matching,
            key=lambda row: Decimal(row.search_relevance) + Decimal(row.commercial_intent_score) / 2,
            default=all_keywords[0],
        )
        if cluster is None:
            cluster = KeywordCluster(
                name=name,
                slug=slug,
                niche=niche,
                cluster_type=cluster_type,
                primary_keyword_id=primary.id,
                intent=intent,
                description=f"Coherent {name.lower()} search cluster for {niche}.",
            )
            db.add(cluster)
            db.flush()
        clusters.append(cluster)
        for row in matching:
            if not db.scalar(
                select(KeywordClusterMember).where(
                    KeywordClusterMember.cluster_id == cluster.id,
                    KeywordClusterMember.keyword_id == row.id,
                )
            ):
                db.add(
                    KeywordClusterMember(
                        cluster_id=cluster.id,
                        keyword_id=row.id,
                        relevance=row.search_relevance,
                        is_primary=row.id == primary.id,
                    )
                )
    db.flush()
    board_count = 0
    for item in config["boards"]:
        if not isinstance(item, dict):
            continue
        name = str(item["name"])
        board = db.scalar(select(PinterestBoard).where(PinterestBoard.name == name, PinterestBoard.niche == niche))
        if board is None:
            board = PinterestBoard(
                external_id=None,
                name=name,
                description=str(item["description"]),
                niche=niche,
                category=str(item.get("category") or "General"),
            )
            db.add(board)
            db.flush()
            board_count += 1
        for term in item.get("keywords", []):
            keyword = upsert_keyword(db, str(term), niche=niche, category=board.category, source="board_taxonomy")
            if not db.scalar(
                select(BoardKeyword).where(BoardKeyword.board_id == board.id, BoardKeyword.keyword_id == keyword.id)
            ):
                db.add(BoardKeyword(board_id=board.id, keyword_id=keyword.id, relevance=Decimal("95")))
    db.commit()
    return {"keywords": len(all_keywords), "clusters": len(clusters), "boards_created": board_count}


def detect_keyword_stuffing(text: str, *, max_repetitions: int = 2) -> list[str]:
    reasons: list[str] = []
    words = re.findall(r"[A-Za-z0-9$]+", text)
    meaningful = [word.lower() for word in words if word.lower() not in STOPWORDS]
    counts = Counter(meaningful)
    if any(count > max_repetitions for count in counts.values()) and len(meaningful) <= 18:
        reasons.append("repeated_keyword")
    alpha = [char for char in text if char.isalpha()]
    if len(words) >= 5 and alpha and sum(char.isupper() for char in alpha) / len(alpha) > 0.65:
        reasons.append("excessive_uppercase")
    if sum(1 for word in meaningful if word in COMMERCIAL_WORDS) >= 4:
        reasons.append("commercial_term_stacking")
    if text.count("!") > 2 or re.search(r"\b(\w+)\s+\1\b", text.lower()):
        reasons.append("unnatural_repetition")
    return sorted(set(reasons))


def score_pin_title(
    title: str,
    *,
    primary_keyword: str,
    intent: str,
    verified_numbers: set[str] | None = None,
    max_repetitions: int = 2,
) -> TitleEvaluation:
    primary_tokens = set(_tokens(primary_keyword))
    title_tokens = set(_tokens(title))
    relevance = Decimal(str(len(primary_tokens & title_tokens) / max(len(primary_tokens), 1) * 100))
    intent_match = Decimal("100") if classify_search_intent(title) == intent else Decimal("72")
    readability = Decimal(str(max(30, 100 - max(len(title) - 70, 0) * 1.4)))
    specificity = Decimal(str(min(100, 52 + len(title_tokens) * 6)))
    commercial = Decimal("88") if intent in {"deal", "budget", "comparison", "purchase_intent"} else Decimal("65")
    unsupported_numbers = {
        item
        for item in re.findall(r"\d+(?:\.\d+)?%?|\$\d+(?:\.\d+)?", title)
        if item not in (verified_numbers or set())
    }
    accurate = Decimal("100") if not unsupported_numbers else Decimal("0")
    stuffing = detect_keyword_stuffing(title, max_repetitions=max_repetitions)
    penalty = Decimal(len(stuffing) * 18)
    score = (
        relevance * Decimal("0.28")
        + intent_match * Decimal("0.17")
        + readability * Decimal("0.16")
        + specificity * Decimal("0.12")
        + commercial * Decimal("0.12")
        + accurate * Decimal("0.15")
        - penalty
    )
    score = max(Decimal("0"), min(Decimal("100"), score)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return TitleEvaluation(
        title=title,
        score=score,
        factors={
            "keyword_relevance": float(relevance),
            "intent_match": float(intent_match),
            "readability": float(readability),
            "specificity": float(specificity),
            "commercial_intent": float(commercial),
            "factual_accuracy": float(accurate),
            "stuffing_detected": bool(stuffing),
            "stuffing_reasons": stuffing,
        },
    )


def generate_title_candidates(
    product: Product,
    primary_keyword: Keyword,
    deal: Deal,
    problem: ProductProblem,
    settings: Settings,
) -> list[TitleEvaluation]:
    keyword = primary_keyword.keyword.title()
    product_short = product.product_name.replace(product.brand or "", "").strip()
    discount = Decimal(product.discount_percent).quantize(Decimal("1"))
    price = Decimal(product.current_price).quantize(Decimal("1"))
    intent = primary_keyword.intent
    by_intent = {
        "deal": [
            f"{product_short} Deal: {discount}% Listed Discount",
            f"{keyword}: Current Price ${price}",
        ],
        "budget": [f"{product_short} Under ${price}", f"{keyword} for a Compact Workspace"],
        "comparison": [f"Best-Fit {product_short} for a Small Desk", f"{keyword}: What to Check"],
        "problem_solution": [f"How This {product_short} Can {problem.solution.title()}", f"{keyword} for Less Clutter"],
        "inspiration": [f"A Practical {keyword} Upgrade", f"Small Desk Setup Idea: {product_short}"],
    }
    titles = by_intent.get(
        intent,
        [f"{keyword}: {product_short}", f"Space-Saving {product_short} for a Small Desk"],
    )
    verified = {str(discount), f"{discount}%", str(price), f"${price}"}
    evaluations = [
        score_pin_title(
            title[:100],
            primary_keyword=primary_keyword.keyword,
            intent=intent,
            verified_numbers=verified,
            max_repetitions=settings.seo_keyword_max_repetitions,
        )
        for title in titles
    ]
    return sorted(evaluations, key=lambda item: item.score, reverse=True)


def select_board(
    db: Session,
    *,
    product: Product,
    keywords: list[Keyword],
    intent: str,
) -> tuple[PinterestBoard, dict[str, float]]:
    boards = db.scalars(select(PinterestBoard).where(PinterestBoard.status == "active")).all()
    if not boards:
        raise ValueError("SEO board taxonomy is empty")
    content_tokens = set(_tokens(" ".join(row.keyword for row in keywords))) | set(_tokens(product.category))
    best: tuple[Decimal, PinterestBoard, dict[str, float]] | None = None
    for board in boards:
        board_terms = db.scalars(
            select(Keyword.keyword)
            .join(BoardKeyword, BoardKeyword.keyword_id == Keyword.id)
            .where(BoardKeyword.board_id == board.id)
        ).all()
        board_tokens = set(_tokens(f"{board.name} {board.description} {' '.join(board_terms)}"))
        overlap = Decimal(str(len(content_tokens & board_tokens) / max(len(content_tokens), 1) * 100))
        category = Decimal("100") if board.category == product.category else Decimal("55")
        intent_fit = Decimal("100") if (intent == "deal" and "deal" in board.name.lower()) else Decimal("75")
        if intent == "budget" and "budget" in board.name.lower():
            intent_fit = Decimal("100")
        historical = min(Decimal("100"), Decimal(board.historical_profit_per_1000) * Decimal("5"))
        score = (
            overlap * Decimal("0.48")
            + category * Decimal("0.25")
            + intent_fit * Decimal("0.20")
            + historical * Decimal("0.07")
        )
        factors = {
            "keyword_overlap": float(overlap),
            "category_fit": float(category),
            "intent_fit": float(intent_fit),
            "historical_profit_signal": float(historical),
            "relevance_score": float(score.quantize(Decimal("0.01"))),
        }
        if best is None or score > best[0]:
            best = (score, board, factors)
    assert best is not None
    return best[1], best[2]


def build_content_brief(db: Session, deal: Deal, settings: Settings, template_key: str) -> ContentBriefPlan:
    seed_seo_taxonomy(db, settings)
    product = deal.product
    associations = db.execute(
        select(ProductKeyword, Keyword)
        .join(Keyword, Keyword.id == ProductKeyword.keyword_id)
        .where(ProductKeyword.product_id == product.id)
    ).all()
    if not associations:
        raise ValueError("No relevant keywords were generated for product")
    ranked = sorted(
        associations,
        key=lambda pair: (
            Decimal(pair[0].product_match)
            * (Decimal(pair[1].commercial_intent_score) + Decimal(pair[1].purchase_intent_score) + 25)
            * (Decimal("1.2") - Decimal(pair[1].competition_estimate) / 100)
        ),
        reverse=True,
    )
    primary = ranked[0][1]
    secondary = [pair[1] for pair in ranked[1:4]]
    cluster = db.scalar(
        select(KeywordCluster)
        .join(KeywordClusterMember, KeywordClusterMember.cluster_id == KeywordCluster.id)
        .where(KeywordClusterMember.keyword_id == primary.id)
        .order_by(KeywordClusterMember.relevance.desc())
        .limit(1)
    )
    if cluster is None:
        cluster = db.scalar(select(KeywordCluster).where(KeywordCluster.niche == settings.niche).limit(1))
    if cluster is None:
        raise ValueError("No keyword cluster is available")
    problem = db.scalar(select(ProductProblem).where(ProductProblem.product_id == product.id).limit(1))
    if problem is None:
        raise ValueError("No product problem/solution record is available")
    board, board_factors = select_board(db, product=product, keywords=[primary, *secondary], intent=primary.intent)
    evaluations = generate_title_candidates(product, primary, deal, problem, settings)
    selected = evaluations[0]
    content_type = "deal" if template_key in {"deal_alert", "price_drop"} or primary.intent == "deal" else "evergreen"
    current_price = Decimal(product.current_price)
    commission = current_price * Decimal(product.expected_commission_rate)
    confidence = min(
        Decimal("95"),
        (Decimal(primary.confidence) + Decimal(problem.confidence) + selected.score) / Decimal("3"),
    ).quantize(Decimal("0.01"))
    return ContentBriefPlan(
        product_id=product.id,
        deal_id=deal.id,
        primary_keyword_id=primary.id,
        keyword_cluster_id=cluster.id,
        board_id=board.id,
        search_intent=primary.intent,
        content_type=content_type,
        target_audience="US shoppers improving a small desk or compact home office",
        problem_solved=problem.problem,
        verified_product_facts={
            "name": product.product_name,
            "brand": product.brand,
            "category": product.category,
            "description": product.description,
            "availability": product.availability,
        },
        price_context={
            "current_price": str(product.current_price),
            "list_price": str(product.list_price) if product.list_price is not None else None,
            "discount_percent": str(product.discount_percent),
            "statistics": deal.price_statistics,
        },
        affiliate_economics={
            "commission_rate": str(product.expected_commission_rate),
            "estimated_commission_per_sale": str(commission.quantize(Decimal("0.01"))),
        },
        recommended_angle=(
            f"{primary.intent.replace('_', ' ')} content connecting {problem.problem} to {problem.solution}"
        ),
        cta="Check the current price and availability",
        disclosure=product.merchant.disclosure_text,
        title_candidates=[
            {"title": item.title, "score": float(item.score), "factors": item.factors} for item in evaluations
        ],
        selected_title=selected.title,
        primary_keyword=primary.keyword,
        secondary_keywords=[row.keyword for row in secondary],
        secondary_keyword_ids=[row.id for row in secondary],
        source="deterministic_commercial_research",
        confidence=confidence,
    )


def persist_content_brief(
    db: Session,
    idea: ContentIdea,
    variant: ContentVariant,
    plan: ContentBriefPlan,
) -> ContentBrief:
    brief = ContentBrief(
        idea_id=idea.id,
        **plan.model_dump(exclude={"primary_keyword", "secondary_keywords", "secondary_keyword_ids"}),
    )
    db.add(brief)
    keyword_ids = [plan.primary_keyword_id, *plan.secondary_keyword_ids]
    for index, keyword_id in enumerate(keyword_ids):
        db.add(
            ContentKeyword(
                content_id=variant.id,
                keyword_id=keyword_id,
                role="primary" if index == 0 else "secondary",
                relevance=Decimal("100") if index == 0 else Decimal("78"),
            )
        )
    return brief


def generate_seo_description(product: Product, deal: Deal, plan: ContentBriefPlan) -> str:
    related = [
        item for item in plan.secondary_keywords if normalize_keyword(item) != normalize_keyword(plan.primary_keyword)
    ][:2]
    related_text = f" Related ideas: {', '.join(related)}." if related else ""
    price_text = ""
    if plan.content_type == "deal":
        price_text = (
            f" Current listed price: ${Decimal(product.current_price):.2f}; "
            f"listed discount: {Decimal(product.discount_percent).quantize(Decimal('1'))}%. "
            f"{deal.price_statistics.get('claim_label', 'Price observed by our system')}."
        )
    description = (
        f"{plan.primary_keyword.capitalize()} for people whose {plan.problem_solved}. "
        f"Based on the listed specifications, {product.product_name} {product.description[:260].rstrip('.').lower()}."
        f"{price_text}{related_text}"
    )
    return re.sub(r"\s+", " ", description).strip()[:800]


def keyword_experiment_result(
    arms: list[dict[str, Decimal | int | str]],
    *,
    minimum_impressions: int,
    minimum_clicks: int,
    minimum_conversions: int,
) -> dict[str, Any]:
    eligible = [
        arm
        for arm in arms
        if int(arm.get("impressions", 0)) >= minimum_impressions
        and int(arm.get("clicks", 0)) >= minimum_clicks
        and int(arm.get("conversions", 0)) >= minimum_conversions
    ]
    if len(eligible) < 2:
        return {
            "status": "insufficient_sample",
            "winner": None,
            "eligible_arms": len(eligible),
            "required": {
                "impressions": minimum_impressions,
                "clicks": minimum_clicks,
                "conversions": minimum_conversions,
            },
        }
    winner = max(eligible, key=lambda arm: Decimal(arm.get("profit", 0)))
    return {"status": "decision_ready", "winner": winner["label"], "optimization_metric": "profit"}


def keyword_summary(db: Session, *, limit: int = 100) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(Keyword)
        .order_by((Keyword.performance_score + Keyword.commercial_intent_score + Keyword.purchase_intent_score).desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": row.id,
            "keyword": row.keyword,
            "normalized_keyword": row.normalized_keyword,
            "category": row.category,
            "intent": row.intent,
            "commercial_intent_score": float(row.commercial_intent_score),
            "purchase_intent_score": float(row.purchase_intent_score),
            "deal_intent_score": float(row.deal_intent_score),
            "search_relevance": float(row.search_relevance),
            "trend_score": float(row.trend_score),
            "competition_estimate": float(row.competition_estimate),
            "performance_score": float(row.performance_score),
            "source": row.source,
            "confidence": float(row.confidence),
        }
        for row in rows
    ]


def seo_taxonomy_summary(db: Session) -> dict[str, Any]:
    clusters = db.scalars(select(KeywordCluster).order_by(KeywordCluster.name)).all()
    boards = db.scalars(select(PinterestBoard).order_by(PinterestBoard.name)).all()
    return {
        "clusters": [
            {
                "id": row.id,
                "name": row.name,
                "type": row.cluster_type,
                "intent": row.intent,
                "keyword_count": int(
                    db.scalar(
                        select(func.count(KeywordClusterMember.id)).where(KeywordClusterMember.cluster_id == row.id)
                    )
                    or 0
                ),
            }
            for row in clusters
        ],
        "boards": [
            {
                "id": row.id,
                "external_id": row.external_id,
                "name": row.name,
                "description": row.description,
                "category": row.category,
                "historical_profit_per_1000": float(row.historical_profit_per_1000),
                "historical_conversion_rate": float(row.historical_conversion_rate),
            }
            for row in boards
        ],
    }
