# Pinterest SEO and discovery

Verified against Pinterest-owned documentation on 2026-08-14.

## Confirmed platform guidance

Pinterest states that discovery occurs through home feed, keyword and visual
search, related Pins, and shopping surfaces. Its business guidance recommends
complete, accurate metadata; relevant keywords in Pin titles, descriptions,
board titles, board descriptions, and linked-page URLs; a relevant board; an
outbound URL; original content; and current catalog availability/category data.
Pinterest also says descriptions help its delivery system determine relevance.

Current documented limits used by DealForge are 100 characters for a title and
800 for a description. Pinterest recommends a 2:3 image ratio such as 1000×1500.
Pinterest warns against repeatedly uploading duplicate Pins. These are enforced
as deterministic constraints or quality gates.

Pinterest Trends can show regional search, save, and shopping trends, related
terms, seasonality, and changes over time. Its charts are normalized indices,
not absolute search-volume estimates. DealForge therefore never labels its
configured `trend_score` as Pinterest search volume.

Official sources:

- [Pin performance and distribution](https://help.pinterest.com/en/business/article/pin-performance-and-distribution)
- [Pinterest content specifications](https://help.pinterest.com/en/business/article/pinterest-product-specs)
- [How content gets discovered](https://business.pinterest.com/en-us/how-to-make-pins/)
- [Pinterest Trends](https://help.pinterest.com/en/business/article/pinterest-trends)
- [Product-feed optimization](https://business.pinterest.com/blog/optimize-your-product-feed-tips/)

## DealForge heuristics—not Pinterest ranking facts

Pinterest does not publish a deterministic organic-ranking formula, absolute
organic keyword volumes, or a guaranteed keyword-density target. DealForge’s
intent scores, competition estimate, title score, cluster weights, board score,
and opportunity score are configurable decision heuristics. Their source and
confidence are stored with the data.

`templates/seo_taxonomy.json` contains the initial niche, boards, seed terms,
problems, thresholds, and versioned opportunity weights. Replace configured
trend hypotheses with observed Pinterest Trends values when available.

## Deterministic workflow

1. Normalize a keyword and classify its likely intent.
2. Generate a small set of product-relevant long tails—never a Cartesian keyword
   explosion.
3. Score relevance, specificity, commercial intent, product match, competition,
   configured trend, and observed DealForge profit performance.
4. Group terms into coherent semantic clusters.
5. Score boards by keyword overlap, category, intent, and historical profit.
6. Produce multiple natural title candidates and reject unverified numbers,
   repeated commercial terms, excessive capitalization, or repetition.
7. Persist a factual content brief before creative generation.
8. Attribute impressions, clicks, conversions, revenue, cost, and profit back to
   each associated keyword.

AI may refine intent or cluster language later, but deterministic validation and
known product facts remain authoritative.

## Demo versus live data

Demo mode uses labeled hypothesis scores and simulated performance. Live search
learning requires a Pinterest business account, Pinterest Analytics access, and
manual or approved-adapter ingestion of Pinterest Trends observations. No live
Pinterest Trends scraper or undocumented endpoint is included.
