# SEO experimentation and learning

Keyword experiments compare coherent alternatives such as:

```text
best monitor arm for small desk
vs.
space-saving monitor arm for small desk
```

Each arm links an experiment to a structured keyword. Metrics derive from the
existing chain:

```text
Keyword → Content → Publication → Impression → Click → Conversion → Revenue → Cost → Profit
```

## Decision metric

The winner is the eligible arm with the highest attributable profit. Impressions,
CTR, saves, and conversions are diagnostic metrics; none overrides profit.

## Sample guard

Defaults are configurable:

```env
SEO_MIN_EXPERIMENT_IMPRESSIONS=500
SEO_MIN_EXPERIMENT_CLICKS=20
SEO_MIN_EXPERIMENT_CONVERSIONS=3
```

At least two arms must independently clear every threshold before a winner is
declared. Otherwise the result is `insufficient_sample`. This prevents one early
sale or a high-impression/zero-revenue Pin from causing large strategy changes.

## Learning views

DealForge reports keyword, price-band, discount-band, and evergreen-versus-deal
performance using CTR, conversion rate, EPC, revenue/profit per 1,000 impressions,
and profit per Pin. The weekly strategy report cites these calculations and marks
whether the overall sample is decision-ready.

AI may later summarize the deterministic evidence. It may not change weights,
budgets, publication permissions, or sample thresholds. Operators should make
small allocations while attribution or reversal data remains incomplete.
