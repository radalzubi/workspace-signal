from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from apps.api.services.affiliate_discovery import JSONAffiliateProgramProvider
from apps.api.services.ingestion import JSONProductProvider

ROOT = Path(__file__).resolve().parents[1]


def test_verified_product_catalog_validates_and_uses_real_merchant_urls() -> None:
    products = JSONProductProvider(ROOT / "templates/verified_products_2026-08-16.json").fetch()
    assert len(products) == 4
    assert {product.merchant for product in products} == {"Anker"}
    assert all(product.canonical_product_url.host == "www.anker.com" for product in products)
    assert all(not product.authorized_image_urls for product in products)
    assert all(product.expected_commission_rate == Decimal("0.08") for product in products)


def test_priority_program_catalog_is_research_only() -> None:
    programs = JSONAffiliateProgramProvider(ROOT / "templates/affiliate_programs_priority_2026-08-16.json").discover()
    assert [program.merchant for program in programs] == ["Anker", "Secretlab", "UPLIFT Desk", "Branch Furniture"]
    assert all(program.status == "research_needed" for program in programs)
    assert all(program.approval_status == "not_applied" for program in programs)
    assert all(program.pinterest_allowed is None for program in programs)
