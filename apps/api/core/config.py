from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated runtime settings; secrets are only read from the environment."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "DealForge"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    public_api_url: str = "http://localhost:8000"
    web_url: str = "http://localhost:3000"
    database_url: str = "sqlite:///./dealforge.db"
    redis_url: str = "redis://localhost:6379/0"
    demo_mode: bool = True
    dry_run: bool = True
    auto_publish: bool = False
    admin_api_key: SecretStr = SecretStr("demo-admin-change-me")
    allowed_origins: str = "http://localhost:3000"
    allowed_hosts: str = "localhost,127.0.0.1,testserver"
    max_upload_bytes: int = 5 * 1024 * 1024

    business_name: str = "Workspace Signal"
    niche: str = "US home-office and workspace upgrades"
    target_country: str = "US"
    currency: str = "USD"
    min_price: Decimal = Decimal("15")
    max_price: Decimal = Decimal("1000")
    min_discount_percent: Decimal = Decimal("15")
    min_posts_per_day: int = 2
    max_posts_per_day: int = 5
    posting_windows: str = "09:00-11:00,14:00-16:00,19:00-21:00"
    timezone: str = "America/New_York"
    deal_max_age_hours: int = 24

    ai_provider: str = "mock"
    openai_api_key: SecretStr | None = None
    openai_model: str = "gpt-5-mini"
    openai_input_cost_per_million: Decimal = Decimal("0.25")
    openai_output_cost_per_million: Decimal = Decimal("2.00")
    daily_ai_budget: Decimal = Decimal("3.00")
    monthly_ai_budget: Decimal = Decimal("50.00")
    tts_provider: str = "disabled"

    storage_provider: str = "local"
    media_root: Path = Path("media/generated")
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    s3_access_key: SecretStr | None = None
    s3_secret_key: SecretStr | None = None

    pinterest_api_base: str = "https://api.pinterest.com/v5"
    pinterest_oauth_base: str = "https://www.pinterest.com/oauth/"
    pinterest_app_id: str | None = None
    pinterest_app_secret: SecretStr | None = None
    pinterest_access_token: SecretStr | None = None
    pinterest_refresh_token: SecretStr | None = None
    pinterest_board_id: str | None = None
    pinterest_redirect_uri: str = "http://localhost:8000/api/v1/integrations/pinterest/callback"

    # Case Lantern is an isolated, human-reviewed short-form video workflow.
    case_lantern_enabled: bool = False
    case_lantern_brand: str = "Case Lantern"
    case_lantern_handle: str = "caselantern"
    case_lantern_human_approval_required: bool = True
    case_lantern_posts_per_day: int = 1
    case_lantern_min_sources: int = 2
    case_lantern_min_words: int = 160
    case_lantern_max_words: int = 225
    tiktok_client_key: str | None = None
    tiktok_client_secret: SecretStr | None = None
    tiktok_redirect_uri: str = "http://localhost:8000/api/v1/integrations/tiktok/callback"
    tiktok_posting_mode: str = "draft"

    enable_tracking_redirect: bool = True
    anonymization_salt: SecretStr = SecretStr("demo-salt-change-me")
    enable_paid_ads: bool = False
    daily_ad_budget: Decimal = Decimal("0")
    monthly_ad_budget: Decimal = Decimal("0")
    max_spend_per_content: Decimal = Decimal("0")
    min_organic_signal_before_promotion: int = 500
    min_ctr: Decimal = Decimal("0.015")
    min_conversion_signal: int = 1

    seo_taxonomy_path: Path = Path("templates/seo_taxonomy.json")
    affiliate_directory_path: Path = Path("templates/affiliate_programs.json")
    seo_min_experiment_impressions: int = 500
    seo_min_experiment_clicks: int = 20
    seo_min_experiment_conversions: int = 3
    seo_keyword_max_repetitions: int = 2
    opportunity_profit_confidence_threshold: Decimal = Decimal("65")
    estimated_media_cost_per_content: Decimal = Decimal("0.03")
    infrastructure_cost_per_content: Decimal = Decimal("0.10")

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        ZoneInfo(value)
        return value

    @field_validator("max_posts_per_day")
    @classmethod
    def sensible_post_limit(cls, value: int) -> int:
        if not 1 <= value <= 20:
            raise ValueError("MAX_POSTS_PER_DAY must be between 1 and 20")
        return value

    @field_validator("case_lantern_posts_per_day")
    @classmethod
    def sensible_case_lantern_limit(cls, value: int) -> int:
        if not 1 <= value <= 3:
            raise ValueError("CASE_LANTERN_POSTS_PER_DAY must be between 1 and 3")
        return value

    @model_validator(mode="after")
    def valid_ranges(self) -> Settings:
        if self.min_price >= self.max_price:
            raise ValueError("MIN_PRICE must be less than MAX_PRICE")
        if self.min_posts_per_day > self.max_posts_per_day:
            raise ValueError("MIN_POSTS_PER_DAY cannot exceed MAX_POSTS_PER_DAY")
        if self.enable_paid_ads and min(self.daily_ad_budget, self.monthly_ad_budget, self.max_spend_per_content) <= 0:
            raise ValueError("Paid ads require all hard budgets to be positive")
        if self.max_upload_bytes < 1024 or self.max_upload_bytes > 25 * 1024 * 1024:
            raise ValueError("MAX_UPLOAD_BYTES must be between 1 KiB and 25 MiB")
        if self.case_lantern_min_words >= self.case_lantern_max_words:
            raise ValueError("CASE_LANTERN_MIN_WORDS must be less than CASE_LANTERN_MAX_WORDS")
        if self.tiktok_posting_mode not in {"draft", "direct"}:
            raise ValueError("TIKTOK_POSTING_MODE must be draft or direct")
        if self.environment.lower() == "production":
            admin_key = self.admin_api_key.get_secret_value()
            salt = self.anonymization_salt.get_secret_value()
            placeholders = {
                "demo-admin-change-me",
                "demo-salt-change-me",
                "replace-with-at-least-32-random-characters",
                "replace-with-a-separate-random-secret",
            }
            if admin_key in placeholders or len(admin_key) < 32:
                raise ValueError("Production ADMIN_API_KEY must be a unique secret of at least 32 characters")
            if salt in placeholders or len(salt) < 32:
                raise ValueError("Production ANONYMIZATION_SALT must be a unique secret of at least 32 characters")
            if "*" in self.origins:
                raise ValueError("Production ALLOWED_ORIGINS cannot contain a wildcard")
            if "*" in self.hosts:
                raise ValueError("Production ALLOWED_HOSTS cannot contain a wildcard")
            if not self.case_lantern_human_approval_required:
                raise ValueError("Production Case Lantern requires human approval")
        return self

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
