from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from apps.api.schemas import UnitEconomicsInput


def calculate_unit_economics(data: UnitEconomicsInput) -> dict[str, Decimal]:
    impressions = Decimal(data.impressions)
    clicks = impressions * data.ctr
    conversions = clicks * data.conversion_rate
    commission_each = data.average_commission or data.average_order_value * data.commission_rate
    revenue = conversions * commission_each
    ad_cost_cpc = clicks * data.ad_cpc
    ad_cost_cpm = impressions / Decimal("1000") * data.ad_cpm
    advertising_cost = max(ad_cost_cpc, ad_cost_cpm)
    total_cost = advertising_cost + data.ai_cost + data.infrastructure_cost
    gross_profit = revenue - total_cost
    cost_per_conversion = total_cost / conversions if conversions else Decimal("0")
    break_even_cpc = data.conversion_rate * commission_each
    break_even_cpm = data.ctr * Decimal("1000") * break_even_cpc
    roas = revenue / advertising_cost if advertising_cost else Decimal("0")
    profit_margin = gross_profit / revenue if revenue else Decimal("0")
    values = {
        "clicks": clicks,
        "conversions": conversions,
        "revenue": revenue,
        "advertising_cost": advertising_cost,
        "total_cost": total_cost,
        "gross_profit": gross_profit,
        "cost_per_conversion": cost_per_conversion,
        "break_even_cpc": break_even_cpc,
        "break_even_cpm": break_even_cpm,
        "roas": roas,
        "profit_margin": profit_margin,
    }
    return {key: value.quantize(Decimal("0.01"), ROUND_HALF_UP) for key, value in values.items()}
