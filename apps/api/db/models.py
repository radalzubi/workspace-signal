from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.db.session import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return str(uuid.uuid4())


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Merchant(TimestampMixin, Base):
    __tablename__ = "merchants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    domain: Mapped[str | None] = mapped_column(String(255))
    quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("75"))
    disclosure_text: Mapped[str] = mapped_column(
        String(255), default="Affiliate link — I may earn a commission from qualifying purchases."
    )
    products: Mapped[list[Product]] = relationship(back_populates="merchant")


class Product(TimestampMixin, Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("provider", "provider_product_id", name="uq_product_provider_id"),
        Index("ix_products_category_availability", "category", "availability"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    provider_product_id: Mapped[str] = mapped_column(String(160))
    product_name: Mapped[str] = mapped_column(String(300), index=True)
    brand: Mapped[str | None] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(160), index=True)
    description: Mapped[str] = mapped_column(Text)
    current_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    list_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    canonical_product_url: Mapped[str] = mapped_column(Text)
    authorized_image_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    authorized_video_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    rating: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    review_count: Mapped[int | None] = mapped_column(Integer)
    availability: Mapped[str] = mapped_column(String(32), default="in_stock", index=True)
    expected_commission_rate: Mapped[Decimal] = mapped_column(Numeric(7, 4), default=0)
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"), index=True)
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    merchant: Mapped[Merchant] = relationship(back_populates="products")
    prices: Mapped[list[ProductPrice]] = relationship(back_populates="product")


class ProductPrice(Base):
    __tablename__ = "product_prices"
    __table_args__ = (Index("ix_product_prices_product_observed", "product_id", "observed_at"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    merchant_id: Mapped[str] = mapped_column(ForeignKey("merchants.id"))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    availability: Mapped[str] = mapped_column(String(32))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    product: Mapped[Product] = relationship(back_populates="prices")


class Deal(TimestampMixin, Base):
    __tablename__ = "deals"
    __table_args__ = (Index("ix_deals_score_active", "deal_score", "status"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    deal_score: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    expected_profit_per_1000: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    score_factors: Mapped[dict[str, Any]] = mapped_column(JSON)
    price_statistics: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(32), default="active")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    product: Mapped[Product] = relationship()


class Asset(TimestampMixin, Base):
    __tablename__ = "assets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), index=True)
    asset_type: Mapped[str] = mapped_column(String(32))
    uri: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(160))
    license: Mapped[str] = mapped_column(String(160))
    authorization: Mapped[str] = mapped_column(String(255))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    checksum: Mapped[str | None] = mapped_column(String(64), index=True)


class ContentIdea(TimestampMixin, Base):
    __tablename__ = "content_ideas"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    deal_id: Mapped[str] = mapped_column(ForeignKey("deals.id"), index=True)
    hook: Mapped[str] = mapped_column(String(300))
    angle: Mapped[str] = mapped_column(String(160))
    title: Mapped[str] = mapped_column(String(300))
    body_copy: Mapped[str] = mapped_column(Text)
    cta: Mapped[str] = mapped_column(String(300))
    hashtags: Mapped[list[str]] = mapped_column(JSON)
    voiceover_script: Mapped[str] = mapped_column(Text)
    visual_sequence: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    target_audience: Mapped[str] = mapped_column(String(255))
    content_category: Mapped[str] = mapped_column(String(100))
    affiliate_disclosure: Mapped[str] = mapped_column(String(300))
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    provider: Mapped[str] = mapped_column(String(64), default="mock")
    deal: Mapped[Deal] = relationship()
    brief: Mapped[ContentBrief | None] = relationship(back_populates="idea", uselist=False)


class ContentVariant(TimestampMixin, Base):
    __tablename__ = "content_variants"
    __table_args__ = (Index("ix_content_queue", "status", "scheduled_for"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    idea_id: Mapped[str] = mapped_column(ForeignKey("content_ideas.id"), index=True)
    template_key: Mapped[str] = mapped_column(String(80), index=True)
    platform: Mapped[str] = mapped_column(String(40), default="pinterest")
    format: Mapped[str] = mapped_column(String(32), default="image")
    caption: Mapped[str] = mapped_column(Text)
    media_uri: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    quality_report: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    winner_state: Mapped[str] = mapped_column(String(32), default="testing")
    idea: Mapped[ContentIdea] = relationship()


class AffiliateLink(TimestampMixin, Base):
    __tablename__ = "affiliate_links"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    content_id: Mapped[str | None] = mapped_column(ForeignKey("content_variants.id"), index=True)
    provider: Mapped[str] = mapped_column(String(80))
    merchant: Mapped[str] = mapped_column(String(160))
    affiliate_id: Mapped[str | None] = mapped_column(String(160))
    original_url: Mapped[str] = mapped_column(Text)
    affiliate_url: Mapped[str] = mapped_column(Text)
    campaign: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    direct_link_required: Mapped[bool] = mapped_column(Boolean, default=False)


class Publication(TimestampMixin, Base):
    __tablename__ = "publications"
    __table_args__ = (UniqueConstraint("platform", "idempotency_key", name="uq_publication_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    content_id: Mapped[str] = mapped_column(ForeignKey("content_variants.id"), index=True)
    affiliate_link_id: Mapped[str] = mapped_column(ForeignKey("affiliate_links.id"))
    platform: Mapped[str] = mapped_column(String(40), index=True)
    external_id: Mapped[str | None] = mapped_column(String(160))
    external_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)


class PerformanceEvent(Base):
    __tablename__ = "performance_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    publication_id: Mapped[str] = mapped_column(ForeignKey("publications.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(32), index=True)
    count: Mapped[int] = mapped_column(Integer, default=1)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Click(Base):
    __tablename__ = "clicks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    affiliate_link_id: Mapped[str] = mapped_column(ForeignKey("affiliate_links.id"), index=True)
    content_id: Mapped[str | None] = mapped_column(ForeignKey("content_variants.id"), index=True)
    platform: Mapped[str | None] = mapped_column(String(40))
    campaign: Mapped[str | None] = mapped_column(String(160))
    referrer: Mapped[str | None] = mapped_column(String(500))
    utm: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    visitor_hash: Mapped[str] = mapped_column(String(64))
    clicked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Conversion(Base):
    __tablename__ = "conversions"
    __table_args__ = (UniqueConstraint("provider", "external_id", name="uq_conversion_external"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    provider: Mapped[str] = mapped_column(String(80))
    external_id: Mapped[str] = mapped_column(String(160))
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), index=True)
    content_id: Mapped[str | None] = mapped_column(ForeignKey("content_variants.id"), index=True)
    campaign: Mapped[str | None] = mapped_column(String(160))
    order_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    commission: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    converted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Cost(Base):
    __tablename__ = "costs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    kind: Mapped[str] = mapped_column(String(40), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    content_id: Mapped[str | None] = mapped_column(ForeignKey("content_variants.id"), index=True)
    campaign_id: Mapped[str | None] = mapped_column(ForeignKey("campaigns.id"), index=True)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    incurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AIUsage(Base):
    __tablename__ = "ai_usage"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    provider: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(120))
    feature: Mapped[str] = mapped_column(String(100), index=True)
    content_id: Mapped[str | None] = mapped_column(ForeignKey("content_variants.id"))
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=0)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Campaign(TimestampMixin, Base):
    __tablename__ = "campaigns"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160), unique=True)
    platform: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)


class Experiment(TimestampMixin, Base):
    __tablename__ = "experiments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160))
    hypothesis: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="running")
    allocation: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class StrategySnapshot(Base):
    __tablename__ = "strategy_snapshots"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    summary: Mapped[str] = mapped_column(Text)
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON)
    scoring_weights: Mapped[dict[str, Any]] = mapped_column(JSON)
    previous_snapshot_id: Mapped[str | None] = mapped_column(ForeignKey("strategy_snapshots.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class JobRun(Base):
    __tablename__ = "job_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_name: Mapped[str] = mapped_column(String(120), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AppSetting(TimestampMixin, Base):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(120), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)


class Keyword(TimestampMixin, Base):
    __tablename__ = "keywords"
    __table_args__ = (
        UniqueConstraint("normalized_keyword", "niche", name="uq_keyword_normalized_niche"),
        Index("ix_keywords_intent_performance", "intent", "performance_score"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    keyword: Mapped[str] = mapped_column(String(240))
    normalized_keyword: Mapped[str] = mapped_column(String(240), index=True)
    niche: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str | None] = mapped_column(String(160), index=True)
    intent: Mapped[str] = mapped_column(String(40), index=True)
    commercial_intent_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    purchase_intent_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    deal_intent_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    search_relevance: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    seasonality: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    trend_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    competition_estimate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=50)
    performance_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    source: Mapped[str] = mapped_column(String(120), default="deterministic")
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=50)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class KeywordCluster(TimestampMixin, Base):
    __tablename__ = "keyword_clusters"
    __table_args__ = (UniqueConstraint("slug", "niche", name="uq_keyword_cluster_slug_niche"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(180), index=True)
    slug: Mapped[str] = mapped_column(String(180))
    niche: Mapped[str] = mapped_column(String(160), index=True)
    cluster_type: Mapped[str] = mapped_column(String(40), default="topic")
    primary_keyword_id: Mapped[str | None] = mapped_column(ForeignKey("keywords.id"), index=True)
    intent: Mapped[str] = mapped_column(String(40), index=True)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)


class KeywordClusterMember(Base):
    __tablename__ = "keyword_cluster_members"
    __table_args__ = (UniqueConstraint("cluster_id", "keyword_id", name="uq_cluster_keyword"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    cluster_id: Mapped[str] = mapped_column(ForeignKey("keyword_clusters.id", ondelete="CASCADE"), index=True)
    keyword_id: Mapped[str] = mapped_column(ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    relevance: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class PinterestBoard(TimestampMixin, Base):
    __tablename__ = "pinterest_boards"
    __table_args__ = (UniqueConstraint("name", "niche", name="uq_board_name_niche"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    external_id: Mapped[str | None] = mapped_column(String(160), unique=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    description: Mapped[str] = mapped_column(Text)
    niche: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str | None] = mapped_column(String(160), index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    historical_profit_per_1000: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    historical_conversion_rate: Mapped[Decimal] = mapped_column(Numeric(8, 5), default=0)


class BoardKeyword(Base):
    __tablename__ = "board_keywords"
    __table_args__ = (UniqueConstraint("board_id", "keyword_id", name="uq_board_keyword"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    board_id: Mapped[str] = mapped_column(ForeignKey("pinterest_boards.id", ondelete="CASCADE"), index=True)
    keyword_id: Mapped[str] = mapped_column(ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    relevance: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=100)


class ProductKeyword(Base):
    __tablename__ = "product_keywords"
    __table_args__ = (UniqueConstraint("product_id", "keyword_id", name="uq_product_keyword"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    keyword_id: Mapped[str] = mapped_column(ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    relevance: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    product_match: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    source: Mapped[str] = mapped_column(String(80), default="deterministic")


class ContentKeyword(Base):
    __tablename__ = "content_keywords"
    __table_args__ = (UniqueConstraint("content_id", "keyword_id", name="uq_content_keyword"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    content_id: Mapped[str] = mapped_column(ForeignKey("content_variants.id", ondelete="CASCADE"), index=True)
    keyword_id: Mapped[str] = mapped_column(ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(24), default="secondary")
    relevance: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)


class ExperimentKeyword(Base):
    __tablename__ = "experiment_keywords"
    __table_args__ = (UniqueConstraint("experiment_id", "keyword_id", "variant_label", name="uq_experiment_keyword"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    experiment_id: Mapped[str] = mapped_column(ForeignKey("experiments.id", ondelete="CASCADE"), index=True)
    keyword_id: Mapped[str] = mapped_column(ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    variant_label: Mapped[str] = mapped_column(String(80))


class ContentBrief(TimestampMixin, Base):
    __tablename__ = "content_briefs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    idea_id: Mapped[str] = mapped_column(ForeignKey("content_ideas.id", ondelete="CASCADE"), unique=True, index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"), index=True)
    deal_id: Mapped[str] = mapped_column(ForeignKey("deals.id"), index=True)
    primary_keyword_id: Mapped[str] = mapped_column(ForeignKey("keywords.id"), index=True)
    keyword_cluster_id: Mapped[str] = mapped_column(ForeignKey("keyword_clusters.id"), index=True)
    board_id: Mapped[str] = mapped_column(ForeignKey("pinterest_boards.id"), index=True)
    search_intent: Mapped[str] = mapped_column(String(40), index=True)
    content_type: Mapped[str] = mapped_column(String(24), index=True)
    target_audience: Mapped[str] = mapped_column(String(255))
    problem_solved: Mapped[str] = mapped_column(String(300))
    verified_product_facts: Mapped[dict[str, Any]] = mapped_column(JSON)
    price_context: Mapped[dict[str, Any]] = mapped_column(JSON)
    affiliate_economics: Mapped[dict[str, Any]] = mapped_column(JSON)
    recommended_angle: Mapped[str] = mapped_column(String(240))
    cta: Mapped[str] = mapped_column(String(240))
    disclosure: Mapped[str] = mapped_column(String(300))
    title_candidates: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    selected_title: Mapped[str] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(80), default="deterministic")
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    idea: Mapped[ContentIdea] = relationship(back_populates="brief")
    board: Mapped[PinterestBoard] = relationship()


class AffiliateProgram(TimestampMixin, Base):
    __tablename__ = "affiliate_programs"
    __table_args__ = (
        UniqueConstraint("network", "program_name", "country", name="uq_affiliate_program_network_name_country"),
        Index("ix_affiliate_programs_status_approval", "status", "approval_status"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    merchant_id: Mapped[str | None] = mapped_column(ForeignKey("merchants.id"), index=True)
    merchant: Mapped[str] = mapped_column(String(180), index=True)
    program_name: Mapped[str] = mapped_column(String(220))
    network: Mapped[str] = mapped_column(String(120), index=True)
    program_url: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="discovered", index=True)
    country: Mapped[str] = mapped_column(String(2), index=True)
    categories: Mapped[list[str]] = mapped_column(JSON, default=list)
    commission_type: Mapped[str] = mapped_column(String(40), default="percent_sale")
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(8, 5), default=0)
    cookie_window: Mapped[int | None] = mapped_column(Integer)
    average_order_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    estimated_conversion_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 5))
    product_feed_available: Mapped[bool] = mapped_column(Boolean, default=False)
    api_available: Mapped[bool] = mapped_column(Boolean, default=False)
    deep_linking_available: Mapped[bool] = mapped_column(Boolean, default=False)
    media_rights: Mapped[str] = mapped_column(String(255), default="unknown")
    social_media_allowed: Mapped[bool | None] = mapped_column(Boolean)
    pinterest_allowed: Mapped[bool | None] = mapped_column(Boolean)
    paid_search_rules: Mapped[str] = mapped_column(Text, default="unknown")
    direct_linking_rules: Mapped[str] = mapped_column(Text, default="unknown")
    conversion_reporting: Mapped[str] = mapped_column(String(160), default="unknown")
    reporting_quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=50)
    payout_threshold: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    payment_frequency: Mapped[str | None] = mapped_column(String(80))
    application_required: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_status: Mapped[str] = mapped_column(String(32), default="not_applied", index=True)
    merchant_reputation_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=50)
    return_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=35)
    terms_last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(Text)
    source_kind: Mapped[str] = mapped_column(String(40), default="official")
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    notes: Mapped[str] = mapped_column(Text, default="")


class AffiliateProgramScore(Base):
    __tablename__ = "affiliate_program_scores"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    program_id: Mapped[str] = mapped_column(ForeignKey("affiliate_programs.id", ondelete="CASCADE"), index=True)
    score_version: Mapped[str] = mapped_column(String(40), default="affiliate-v1")
    attractiveness_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), index=True)
    expected_revenue_per_100_clicks: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    components: Mapped[dict[str, Any]] = mapped_column(JSON)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ProductProblem(TimestampMixin, Base):
    __tablename__ = "product_problems"
    __table_args__ = (UniqueConstraint("product_id", "normalized_problem", name="uq_product_problem"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    problem: Mapped[str] = mapped_column(String(300))
    normalized_problem: Mapped[str] = mapped_column(String(300))
    solution: Mapped[str] = mapped_column(String(300))
    relevance_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    source: Mapped[str] = mapped_column(String(80), default="deterministic")
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)


class ProductOpportunity(TimestampMixin, Base):
    __tablename__ = "product_opportunities"
    __table_args__ = (Index("ix_opportunities_rank", "rank_basis", "expected_profit_per_1000", "opportunity_score"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    affiliate_program_id: Mapped[str | None] = mapped_column(ForeignKey("affiliate_programs.id"), index=True)
    keyword_cluster_id: Mapped[str | None] = mapped_column(ForeignKey("keyword_clusters.id"), index=True)
    board_id: Mapped[str | None] = mapped_column(ForeignKey("pinterest_boards.id"), index=True)
    score_version: Mapped[str] = mapped_column(String(40), default="opportunity-v1")
    weights_version: Mapped[int] = mapped_column(Integer, default=1)
    opportunity_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), index=True)
    rank_basis: Mapped[str] = mapped_column(String(32), default="opportunity_score", index=True)
    components: Mapped[dict[str, Any]] = mapped_column(JSON)
    expected_impressions: Mapped[int] = mapped_column(Integer, default=0)
    expected_ctr: Mapped[Decimal] = mapped_column(Numeric(8, 5), default=0)
    expected_conversion_rate: Mapped[Decimal] = mapped_column(Numeric(8, 5), default=0)
    expected_order_value: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    commission_rate: Mapped[Decimal] = mapped_column(Numeric(8, 5), default=0)
    expected_revenue_per_1000: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    expected_cost_per_1000: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    expected_profit_per_1000: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0, index=True)
    expected_profit_low: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    expected_profit_high: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    price_band: Mapped[str] = mapped_column(String(32), index=True)
    discount_band: Mapped[str] = mapped_column(String(32), index=True)
    saturation_penalty: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    risk_penalty: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    recommended_angle: Mapped[str] = mapped_column(String(240))
    selection_reason: Mapped[str] = mapped_column(Text)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class ProductWatchlist(TimestampMixin, Base):
    __tablename__ = "product_watchlists"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(180))
    product_id: Mapped[str | None] = mapped_column(ForeignKey("products.id"), index=True)
    merchant_id: Mapped[str | None] = mapped_column(ForeignKey("merchants.id"), index=True)
    category: Mapped[str | None] = mapped_column(String(160), index=True)
    rule_type: Mapped[str] = mapped_column(String(40), index=True)
    threshold: Mapped[Decimal] = mapped_column(Numeric(12, 4))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    last_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4))
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class KeywordPerformance(Base):
    __tablename__ = "keyword_performance"
    __table_args__ = (Index("ix_keyword_performance_period", "keyword_id", "period_end"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    keyword_id: Mapped[str] = mapped_column(ForeignKey("keywords.id", ondelete="CASCADE"), index=True)
    content_id: Mapped[str | None] = mapped_column(ForeignKey("content_variants.id", ondelete="CASCADE"), index=True)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    profit: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source: Mapped[str] = mapped_column(String(80), default="derived")
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)


class MediaBrand(TimestampMixin, Base):
    __tablename__ = "media_brands"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(40), default="tiktok")
    handle: Mapped[str] = mapped_column(String(100), index=True)
    niche: Mapped[str] = mapped_column(String(200))
    audience: Mapped[str] = mapped_column(String(300))
    bio: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    brand_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    human_approval_required: Mapped[bool] = mapped_column(Boolean, default=True)


class StoryProject(TimestampMixin, Base):
    __tablename__ = "story_projects"
    __table_args__ = (Index("ix_story_projects_queue", "status", "scheduled_for"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    brand_id: Mapped[str] = mapped_column(ForeignKey("media_brands.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(300))
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    story_type: Mapped[str] = mapped_column(String(60), default="historical_case")
    status: Mapped[str] = mapped_column(String(32), default="research", index=True)
    hook: Mapped[str] = mapped_column(String(400))
    synopsis: Mapped[str] = mapped_column(Text)
    script: Mapped[str] = mapped_column(Text)
    caption: Mapped[str] = mapped_column(Text)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=75)
    risk_level: Mapped[str] = mapped_column(String(32), default="low")
    factual_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    quality_report: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    visual_plan: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    voice_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    media_uri: Mapped[str | None] = mapped_column(Text)
    export_uri: Mapped[str | None] = mapped_column(Text)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StorySource(TimestampMixin, Base):
    __tablename__ = "story_sources"
    __table_args__ = (UniqueConstraint("project_id", "url", name="uq_story_source_url"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("story_projects.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(300))
    publisher: Mapped[str] = mapped_column(String(160))
    source_type: Mapped[str] = mapped_column(String(60), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    credibility_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")


class StoryClaim(TimestampMixin, Base):
    __tablename__ = "story_claims"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("story_projects.id", ondelete="CASCADE"), index=True)
    claim_text: Mapped[str] = mapped_column(Text)
    source_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="supported", index=True)
    risk_category: Mapped[str] = mapped_column(String(60), default="historical_fact")
    notes: Mapped[str] = mapped_column(Text, default="")


class SocialPublication(TimestampMixin, Base):
    __tablename__ = "social_publications"
    __table_args__ = (UniqueConstraint("platform", "idempotency_key", name="uq_social_publication_key"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    project_id: Mapped[str] = mapped_column(ForeignKey("story_projects.id", ondelete="CASCADE"), index=True)
    platform: Mapped[str] = mapped_column(String(40), default="tiktok", index=True)
    mode: Mapped[str] = mapped_column(String(20), default="draft")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    external_id: Mapped[str | None] = mapped_column(String(160))
    external_url: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
