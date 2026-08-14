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
