from decimal import Decimal

from apps.api.schemas import UnitEconomicsInput
from apps.api.services.economics import calculate_unit_economics


def test_unit_economics_profit_and_break_even() -> None:
    result = calculate_unit_economics(
        UnitEconomicsInput(
            impressions=100_000,
            ctr=Decimal("0.02"),
            conversion_rate=Decimal("0.04"),
            average_order_value=Decimal("80"),
            commission_rate=Decimal("0.05"),
            ad_cpc=Decimal("0"),
            ai_cost=Decimal("10"),
            infrastructure_cost=Decimal("40"),
        )
    )
    assert result["revenue"] == Decimal("320.00")
    assert result["gross_profit"] == Decimal("270.00")
    assert result["break_even_cpc"] == Decimal("0.16")
