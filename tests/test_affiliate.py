from urllib.parse import parse_qs, urlparse

import pytest

from apps.api.services.affiliate import UTMDirectLinkProvider


def test_affiliate_url_preserves_existing_query_and_adds_transparent_attribution() -> None:
    result = UTMDirectLinkProvider().build(
        "https://merchant.example/item?color=black", "partner-1", "desk-deals", "content-1"
    )
    query = parse_qs(urlparse(result).query)
    assert query["color"] == ["black"]
    assert query["affiliate_id"] == ["partner-1"]
    assert query["utm_content"] == ["content-1"]


def test_affiliate_url_rejects_non_http_destination() -> None:
    with pytest.raises(ValueError):
        UTMDirectLinkProvider().build("javascript:alert(1)", None, "campaign", "content")
