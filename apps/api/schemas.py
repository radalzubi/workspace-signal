from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProductObservation(BaseModel):
    provider: str
    provider_product_id: str
    product_name: str
    brand: str | None = None
    category: str
    description: str
    current_price: Decimal = Field(gt=0)
    list_price: Decimal | None = Field(default=None, gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    canonical_product_url: HttpUrl
    authorized_image_urls: list[HttpUrl] = Field(default_factory=list)
    authorized_video_urls: list[HttpUrl] = Field(default_factory=list)
    rating: Decimal | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    availability: Literal["in_stock", "out_of_stock", "unknown"] = "in_stock"
    merchant: str
    merchant_domain: str | None = None
    expected_commission_rate: Decimal = Field(default=Decimal("0.04"), ge=0, le=1)
    observed_at: datetime

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class ContentStrategy(BaseModel):
    hook: str = Field(max_length=220)
    angle: str = Field(max_length=160)
    title: str = Field(max_length=100)
    body_copy: str = Field(max_length=800)
    cta: str = Field(max_length=180)
    hashtags: list[str] = Field(min_length=3, max_length=12)
    voiceover_script: str = Field(max_length=1200)
    visual_sequence: list[dict[str, Any]] = Field(min_length=3, max_length=8)
    target_audience: str
    content_category: str
    affiliate_disclosure: str
    confidence_score: Decimal = Field(ge=0, le=100)


class ProductOut(ORMModel):
    id: str
    product_name: str
    category: str
    current_price: Decimal
    list_price: Decimal | None
    discount_percent: Decimal
    currency: str
    availability: str


class DealOut(ORMModel):
    id: str
    deal_score: Decimal
    expected_profit_per_1000: Decimal
    score_factors: dict[str, Any]
    price_statistics: dict[str, Any]
    status: str
    expires_at: datetime
    product: ProductOut


class ContentOut(ORMModel):
    id: str
    template_key: str
    platform: str
    format: str
    caption: str
    media_uri: str | None
    status: str
    quality_report: dict[str, Any]
    scheduled_for: datetime | None
    winner_state: str


class QueueUpdate(BaseModel):
    action: Literal["approve", "reject", "regenerate", "publish", "schedule"]
    caption: str | None = Field(default=None, max_length=800)
    affiliate_url: HttpUrl | None = None
    scheduled_for: datetime | None = None


class UnitEconomicsInput(BaseModel):
    impressions: int = Field(ge=0)
    ctr: Decimal = Field(ge=0, le=1)
    conversion_rate: Decimal = Field(ge=0, le=1)
    average_order_value: Decimal = Field(ge=0)
    commission_rate: Decimal = Field(ge=0, le=1)
    average_commission: Decimal | None = Field(default=None, ge=0)
    ad_cpc: Decimal = Field(default=Decimal("0"), ge=0)
    ad_cpm: Decimal = Field(default=Decimal("0"), ge=0)
    ai_cost: Decimal = Field(default=Decimal("0"), ge=0)
    infrastructure_cost: Decimal = Field(default=Decimal("0"), ge=0)


class OnboardingInput(BaseModel):
    business_name: str = Field(min_length=2, max_length=120)
    niche: str = Field(min_length=3, max_length=160)
    country: str = Field(min_length=2, max_length=2)
    currency: str = Field(min_length=3, max_length=3)
    affiliate_provider: str
    pinterest_board_id: str | None = None
    posts_per_day: int = Field(ge=1, le=10)
    ai_provider: Literal["mock", "openai"] = "mock"
    tts_provider: str = "disabled"
    monthly_software_budget: Decimal = Field(gt=0)
    monthly_ad_budget: Decimal = Field(default=Decimal("0"), ge=0)
