# Opportunity scoring and expected profit

The opportunity engine separates a 0–100 explainable score from expected profit.

## Versioned explainable score

Positive components are configured in `templates/seo_taxonomy.json`:

```text
Deal quality
+ Search demand proxy
+ Commercial intent
+ Affiliate economics
+ Content potential
+ Historical performance
+ Problem/solution value
- Competition penalty
- Saturation penalty
- Risk penalty
```

The persisted record stores component values, weight version, score version,
keyword, intent, board relevance, historical inputs, saturation, risk, and the
selection explanation. Configuration changes produce a new calculated record so
historical decisions remain reviewable.

## Expected economics

For 1,000 impressions:

```text
Expected clicks = 1,000 × expected CTR
Expected conversions = expected clicks × expected conversion rate
Expected revenue = expected conversions × expected order value × commission rate
Expected profit = expected revenue - media/AI/infrastructure/advertising allocation
```

Observed CTR and conversion rates are blended with intent priors. Observations
receive more weight as samples grow. Program AOV/rate are used when an eligible
program record exists; otherwise product-feed estimates are used and confidence
falls.

## Confidence-aware ranking

Each result includes expected profit, a conservative/optimistic interval, and a
0–100 confidence score. Confidence reflects traffic and conversion sample size,
keyword-source confidence, program completeness, and policy certainty.

If confidence meets `OPPORTUNITY_PROFIT_CONFIDENCE_THRESHOLD`, ranking uses
expected profit. Otherwise it uses the explainable opportunity score. This avoids
false precision during early operation.

## Dashboard interpretation

The Opportunities page shows price context, program, commission per sale, search
and intent signals, expected CTR/conversion/EPC/profit, interval, confidence,
score breakdown, saturation, risk, keyword cluster, board, angle, and selection
reason. It is an allocation interface—not a generic product catalog.
