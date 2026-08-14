# Profitable product discovery

Product discovery extends the existing authorized feed pipeline. It does not
scrape retailers or create products from unverifiable web pages.

## Commercial research sequence

```text
Authorized product observation
→ price history and availability
→ affiliate-program fit
→ keyword and intent match
→ problem/solution mapping
→ saturation and risk
→ expected economics
→ opportunity ranking
→ persisted content brief
```

The system evaluates verified discount, 7/30/90-day price context, expected
commission, estimated conversion, order value, category performance, keyword
intent, board relevance, visual/content potential, product availability,
merchant/program quality, seasonality hypotheses, competition, prior profit, and
publication saturation.

## Problem/solution records

Each product can map to a concrete problem and solution. Demo examples include a
monitor arm for recovering desk surface, cable routing for clutter, and an
under-desk drawer for missing storage. These records influence long-tail terms,
content angles, and content-potential scoring. They do not permit unsupported
product claims.

## Saturation

The 30-day penalty counts recent promotion of the product and category. A product
can return when a new calculation shows material price, intent, seasonality,
angle, or performance value; the score is recalculated instead of imposing a
permanent ban.

## Watchlists

Supported deterministic rules are:

- Product/category price at least a configured percentage below its 30-day average.
- Product/category opportunity score above a threshold.
- Product/merchant/category commission rate above a threshold.

Celery evaluates active rules hourly and records the last value, evaluation time,
and trigger time. Watchlists alert research; they do not publish or spend money.

## External data requirements

Reliable production ranking requires an authorized product feed/API, current
price and stock, confirmed commission terms, conversion/reversal imports, media
rights, and real Pinterest search/analytics observations. With missing data,
DealForge reduces confidence and ranks by the explainable score rather than
pretending the expected-profit estimate is precise.
