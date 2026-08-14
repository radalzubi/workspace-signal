from __future__ import annotations

import base64
import hashlib
import mimetypes
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

from apps.api.core.config import Settings
from apps.api.core.crypto import decrypt_json
from apps.api.db.models import AffiliateLink, AppSetting, ContentVariant, Publication
from apps.api.services.affiliate import outbound_url
from apps.api.services.quality import validate_content


class TransientProviderError(RuntimeError):
    pass


class SocialPublisher(ABC):
    @abstractmethod
    def discover_destinations(self) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def publish(self, variant: ContentVariant, link: AffiliateLink) -> dict[str, Any]:
        raise NotImplementedError


class DryRunPublisher(SocialPublisher):
    def __init__(self, platform: str = "pinterest") -> None:
        self.platform = platform

    def discover_destinations(self) -> list[dict[str, Any]]:
        return [{"id": "demo-board", "name": "Small-Space Desk Finds", "privacy": "PUBLIC"}]

    def publish(self, variant: ContentVariant, link: AffiliateLink) -> dict[str, Any]:
        external_id = f"dry_{variant.id[:12]}"
        return {
            "id": external_id,
            "url": f"dry-run://{self.platform}/{external_id}",
            "dry_run": True,
        }


class PinterestPublisher(SocialPublisher):
    """Pinterest API v5 publisher for original image/video Pins."""

    def __init__(self, settings: Settings, access_token: str | None = None) -> None:
        token = access_token or (
            settings.pinterest_access_token.get_secret_value() if settings.pinterest_access_token else None
        )
        if not token:
            raise ValueError("PINTEREST_ACCESS_TOKEN is required for live publishing")
        self.settings = settings
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    @retry(
        retry=retry_if_exception_type((httpx.TimeoutException, TransientProviderError)),
        wait=wait_exponential_jitter(initial=1, max=20),
        stop=stop_after_attempt(4),
        reraise=True,
    )
    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        with httpx.Client(timeout=20) as client:
            response = client.request(
                method, f"{self.settings.pinterest_api_base}{path}", headers=self.headers, **kwargs
            )
        if response.status_code == 429 or response.status_code >= 500:
            raise TransientProviderError(f"Pinterest transient error {response.status_code}")
        if response.status_code == 401:
            raise PermissionError("Pinterest token is invalid or expired")
        response.raise_for_status()
        return response

    def discover_destinations(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/boards", params={"page_size": 100}).json()
        return cast(list[dict[str, Any]], payload.get("items", []))

    def publish(self, variant: ContentVariant, link: AffiliateLink) -> dict[str, Any]:
        if not self.settings.pinterest_board_id:
            raise ValueError("PINTEREST_BOARD_ID is required")
        if not variant.media_uri:
            raise ValueError("Rendered media is required")
        media_path = self.settings.media_root.resolve() / Path(variant.media_uri).name
        if self.settings.media_root.resolve() not in media_path.parents or not media_path.exists():
            raise ValueError("Media path is invalid")
        mime = mimetypes.guess_type(media_path.name)[0] or "image/png"
        if not mime.startswith("image/"):
            raise ValueError("Live MVP publisher supports image Pins; video stays export-ready")
        payload = {
            "board_id": self.settings.pinterest_board_id,
            "title": variant.idea.title[:100],
            "description": variant.caption[:800],
            "link": outbound_url(link, self.settings),
            "alt_text": f"Deal graphic for {variant.idea.deal.product.product_name}"[:500],
            "media_source": {
                "source_type": "image_base64",
                "content_type": mime,
                "data": base64.b64encode(media_path.read_bytes()).decode(),
            },
        }
        return cast(dict[str, Any], self._request("POST", "/pins", json=payload).json())


class ExportOnlyPublisher(SocialPublisher):
    """Manual-post package for platforms whose approved API access is not configured."""

    def __init__(self, platform: str) -> None:
        self.platform = platform

    def discover_destinations(self) -> list[dict[str, Any]]:
        return []

    def publish(self, variant: ContentVariant, link: AffiliateLink) -> dict[str, Any]:
        return {
            "id": None,
            "url": None,
            "export_ready": True,
            "platform": self.platform,
            "media": variant.media_uri,
            "caption": variant.caption,
        }


def _stored_pinterest_token(db: Session, settings: Settings) -> str | None:
    row = db.get(AppSetting, "credential:pinterest")
    if not row:
        return None
    encrypted = row.value.get("encrypted")
    if not isinstance(encrypted, str):
        return None
    payload = decrypt_json(encrypted, settings.admin_api_key.get_secret_value())
    token = payload.get("access_token")
    return token if isinstance(token, str) else None


def publisher_for(db: Session, settings: Settings, platform: str = "pinterest") -> SocialPublisher:
    if platform != "pinterest":
        return ExportOnlyPublisher(platform)
    if settings.dry_run:
        return DryRunPublisher(platform)
    return PinterestPublisher(settings, _stored_pinterest_token(db, settings))


def publish_variant(db: Session, variant: ContentVariant, link: AffiliateLink, settings: Settings) -> Publication:
    idempotency_key = hashlib.sha256(f"{variant.id}|{variant.platform}".encode()).hexdigest()
    prior = db.scalar(
        select(Publication).where(
            Publication.platform == variant.platform,
            Publication.idempotency_key == idempotency_key,
        )
    )
    if prior and prior.status in {"published", "dry_run"}:
        variant.status = "published" if prior.status == "published" else "dry_run"
        db.commit()
        return prior
    report = validate_content(db, variant, settings)
    if not report["passed"]:
        raise ValueError(f"Quality gate failed: {report['errors']}")
    if not settings.auto_publish and variant.status != "approved":
        raise PermissionError("Content must be approved while AUTO_PUBLISH=false")
    publisher = publisher_for(db, settings, variant.platform)
    try:
        result = publisher.publish(variant, link)
        status = "dry_run" if result.get("dry_run") or result.get("export_ready") else "published"
        publication = prior or Publication(
            content_id=variant.id,
            affiliate_link_id=link.id,
            platform=variant.platform,
            idempotency_key=idempotency_key,
            status=status,
        )
        publication.external_id = result.get("id")
        publication.external_url = result.get("url")
        publication.status = status
        publication.published_at = datetime.now(UTC)
        publication.error = None
        variant.status = "published" if status == "published" else "dry_run"
    except Exception as exc:
        publication = prior or Publication(
            content_id=variant.id,
            affiliate_link_id=link.id,
            platform=variant.platform,
            idempotency_key=idempotency_key,
            status="failed",
        )
        publication.status = "failed"
        publication.error = str(exc)[:2000]
        db.add(publication)
        db.commit()
        raise
    db.add(publication)
    db.commit()
    return publication
