from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.core.config import Settings
from apps.api.db.models import AffiliateLink, ContentVariant


class AffiliateLinkProvider(ABC):
    @abstractmethod
    def build(self, original_url: str, affiliate_id: str | None, campaign: str, content_id: str) -> str:
        raise NotImplementedError


class UTMDirectLinkProvider(AffiliateLinkProvider):
    """Adds transparent attribution parameters; provider-specific tags can replace this."""

    def build(self, original_url: str, affiliate_id: str | None, campaign: str, content_id: str) -> str:
        parsed = urlparse(original_url)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Affiliate destination must be HTTP(S)")
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query.update(
            {
                "utm_source": "pinterest",
                "utm_medium": "affiliate_social",
                "utm_campaign": campaign,
                "utm_content": content_id,
            }
        )
        if affiliate_id:
            query["affiliate_id"] = affiliate_id
        return urlunparse(parsed._replace(query=urlencode(query)))


def ensure_affiliate_link(
    db: Session,
    variant: ContentVariant,
    settings: Settings,
    affiliate_id: str | None = None,
) -> AffiliateLink:
    existing = db.scalar(select(AffiliateLink).where(AffiliateLink.content_id == variant.id))
    if existing:
        return existing
    product = variant.idea.deal.product
    campaign = f"{settings.niche.lower().replace(' ', '-')[:45]}-{variant.template_key}"
    destination = UTMDirectLinkProvider().build(product.canonical_product_url, affiliate_id, campaign, variant.id)
    slug = hashlib.sha256(f"{variant.id}|{destination}".encode()).hexdigest()[:12]
    link = AffiliateLink(
        product_id=product.id,
        content_id=variant.id,
        provider=product.provider,
        merchant=product.merchant.name,
        affiliate_id=affiliate_id,
        original_url=product.canonical_product_url,
        affiliate_url=destination,
        campaign=campaign,
        slug=slug,
    )
    db.add(link)
    db.commit()
    return link


def outbound_url(link: AffiliateLink, settings: Settings) -> str:
    if settings.enable_tracking_redirect and not link.direct_link_required:
        return f"{settings.public_api_url}/go/{link.slug}"
    return link.affiliate_url
