# DealForge SEO and affiliate-profit operating guide

Last validated: 2026-08-14

## Mission

DealForge now optimizes this measurable chain:

```text
Pinterest discovery
→ relevant product content
→ high-intent outbound click
→ attributed purchase
→ commission
→ profit
```

Impressions, saves, clicks, and conversion rate remain useful diagnostics. The
allocation target is attributable profit, with confidence-aware fallbacks while
the sample is small.

## What is implemented

- Structured keyword records, semantic clusters, product/content/board links,
  search-intent classification, long-tail generation, title scoring, keyword-
  stuffing checks, board selection, factual content briefs, and keyword-level
  attribution.
- Configurable niche and board taxonomy for US small-space desk setups. The niche
  lives in `templates/seo_taxonomy.json`; business logic is not niche-specific.
- Structured affiliate-program research, safe JSON imports, policy/economics
  fields, risk-adjusted attractiveness scores, score history, and confidence.
- Product opportunity scoring that combines verified deal quality, intent,
  affiliate economics, content potential, performance, competition, saturation,
  and risk.
- Expected clicks, conversions, affiliate revenue, EPC, profit per 1,000
  impressions, confidence, and conservative/optimistic profit bounds.
- Price-band, discount-band, evergreen/deal, keyword, and board learning.
- Minimum-sample SEO experiments and deterministic weekly strategy reports.
- Product/category/merchant watchlists with hourly Celery reevaluation.
- Dashboard views for Opportunities, SEO Intelligence, Affiliate Programs, and
  Strategy Report.
- A complete demo journey with deliberately different SEO/economic outcomes.

## Architecture boundary

Deterministic code owns normalization, price statistics, attribution, financial
math, program/opportunity scoring, sample thresholds, watchlists, disclosure and
publication checks, factual-number validation, and confidence gates.

AI may interpret intent, suggest semantic clusters and content angles, write
natural titles/descriptions, and summarize strategy evidence. Creative output is
constrained by a persisted content brief and validated against known product
facts. AI cannot rewrite scoring weights, publication permissions, or budgets.

External data supplies current inventory and prices, official affiliate terms,
media rights, network reporting, Pinterest analytics, and Pinterest Trends
observations. Missing or unconfirmed inputs reduce confidence.

## Pinterest facts and DealForge heuristics

Pinterest-owned guidance says relevant keywords may be used in Pin titles,
descriptions, board titles, board descriptions, and linked-page URLs; content
should use a relevant board, current metadata, an outbound URL, and original
creative. Current documented limits are 100 title characters and 800 description
characters, and the recommended image shape is 2:3 such as 1000×1500. Pinterest
also discourages repeated duplicate Pins.

Pinterest Trends provides normalized regional indices, related terms, and
seasonality—not absolute organic search volume. DealForge therefore labels its
configured trend and competition values as hypotheses or observed inputs, never
as Pinterest ranking facts.

Official references:

- https://help.pinterest.com/en/business/article/pin-performance-and-distribution
- https://help.pinterest.com/en/business/article/pinterest-product-specs
- https://business.pinterest.com/en-us/how-to-make-pins/
- https://help.pinterest.com/en/business/article/pinterest-trends
- https://business.pinterest.com/blog/optimize-your-product-feed-tips/

Pinterest does not publish an organic ranking formula, guaranteed keyword
density, or absolute organic keyword volume. Intent scores, title scores, board
relevance, competition, and opportunity weights are versioned DealForge
heuristics that should be recalibrated with attributed performance.

## SEO workflow

1. Normalize each term with Unicode normalization, lowercase conversion,
   punctuation cleanup, and whitespace collapse.
2. Classify the likely intent: informational, inspiration, problem solution,
   product discovery, comparison, budget, deal, purchase intent, or brand
   specific.
3. Generate only relevant product/use-case/audience/price/problem/benefit long
   tails; reject incoherent combinations.
4. Score relevance, specificity, commercial intent, product match, competition,
   configured trend, and observed DealForge profit performance.
5. Associate coherent clusters with products, content, boards, and experiments.
6. Score boards by semantic overlap, category, intent, and historical profit.
7. Create several natural titles and reject stuffing, excessive capitalization,
   duplication, and numbers not present in verified product/deal facts.
8. Persist a content brief before generation. It includes product, primary and
   secondary terms, intent, audience, problem, verified facts, price, economics,
   angle, board, CTA, and disclosure.
9. Attribute publication performance and profit back to each linked keyword.

## Affiliate-program discovery

The implemented adapter imports a validated JSON research directory with a 5 MB
limit and idempotent program identity. It never applies to a program or accepts a
contract. Bundled programs are explicitly fictional demo records.

Potential production sources have documented adapter boundaries but no mocked
live behavior:

- Impact Partner APIs: https://integrations.impact.com/impact-publisher
- Awin publisher APIs/feeds: https://help.awin.com/apidocs/for-publishers
- CJ publisher paths: https://docs.cj.com/docs/finding-your-path
- Amazon Creators API: https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction

Each source requires the operator's account, approval, credentials, applicable
merchant relationships, current terms review, and permitted product/media use.
DealForge does not assume acceptance or Pinterest permission.

Program scoring considers commission value, conversion probability, AOV,
catalog/feed/API/deep-link quality, category fit, Pinterest suitability,
reporting, reputation, cookie duration, returns, media rights, geography,
approval, and status. Unknown permission or rights reduce both score and
confidence.

```text
Expected revenue per 100 clicks
= 100 × conversion rate × average order value × commission rate
```

Before enabling a program, record the official source, `terms_last_checked`,
social/Pinterest rules, redirect/deep-link rules, media license, commission
groups, reversal behavior, geography, tax/payment requirements, and reporting
identifiers.

## Product opportunity model

The configurable explainable score is:

```text
Deal quality
+ search-demand proxy
+ commercial intent
+ affiliate economics
+ content potential
+ historical performance
+ problem/solution value
- competition penalty
- saturation penalty
- risk penalty
```

Weights and their version live in `templates/seo_taxonomy.json`. Every persisted
result retains its component breakdown, score version, weight version, keyword,
intent, board, performance inputs, confidence, and explanation.

For 1,000 impressions:

```text
Expected clicks = 1,000 × expected CTR
Expected conversions = expected clicks × expected conversion rate
Expected affiliate revenue
  = expected conversions × expected order value × commission rate
Expected profit
  = expected affiliate revenue
  - AI/media/infrastructure/advertising allocation
EPC = expected affiliate revenue ÷ expected clicks
```

Observed CTR/CVR is blended with priors and gains weight as samples grow. When
confidence reaches `OPPORTUNITY_PROFIT_CONFIDENCE_THRESHOLD`, ranking uses
expected profit; otherwise it uses the explainable score. Every row includes a
confidence score and profit interval to expose uncertainty.

The saturation penalty measures recent product/category promotion. A product
may return after a material price change, a new content angle, strong prior
performance, seasonality, or demand change; there is no permanent ban.

## Experiments and learning

```text
Keyword → Content → Publication → Impression → Click
→ Conversion → Revenue → Cost → Profit
```

An experiment arm is eligible only after meeting all configured defaults:

```env
SEO_MIN_EXPERIMENT_IMPRESSIONS=500
SEO_MIN_EXPERIMENT_CLICKS=20
SEO_MIN_EXPERIMENT_CONVERSIONS=3
```

At least two arms must clear every threshold. The eligible arm with the highest
attributable profit wins; otherwise the status remains `insufficient_sample`.
Weekly reports use actual keyword, price-band, discount-band, content-type, and
board evidence. AI may summarize that evidence but cannot manufacture it.

## Database additions

- `keywords`, `keyword_clusters`, `keyword_cluster_members`
- `pinterest_boards`, `board_keywords`
- `product_keywords`, `content_keywords`, `experiment_keywords`
- `content_briefs`
- `affiliate_programs`, `affiliate_program_scores`
- `product_problems`, `product_opportunities`, `product_watchlists`
- `keyword_performance`

Apply the migration with:

```bash
.venv/bin/alembic upgrade head
```

## API and background jobs

Read endpoints:

```text
GET /api/v1/opportunities
GET /api/v1/seo/keywords
GET /api/v1/seo/taxonomy
GET /api/v1/seo/analytics
GET /api/v1/seo/content-briefs
GET /api/v1/seo/experiments
GET /api/v1/affiliate-programs
GET /api/v1/affiliate-programs/discovery-sources
GET /api/v1/watchlists
GET /api/v1/reports/search-strategy
```

Admin mutation endpoints:

```text
POST  /api/v1/opportunities/refresh
POST  /api/v1/affiliate-programs/import
POST  /api/v1/affiliate-programs/rescore
POST  /api/v1/watchlists
POST  /api/v1/watchlists/evaluate
PATCH /api/v1/seo/boards/{id}?external_id={pinterest_board_id}
```

Celery refreshes SEO/commercial learning daily and evaluates active watchlists
hourly. Watchlist triggers record evidence; they do not publish or spend money.

## Configuration

Important environment variables:

```env
SEO_TAXONOMY_PATH=templates/seo_taxonomy.json
AFFILIATE_DIRECTORY_PATH=templates/affiliate_programs.json
SEO_MIN_EXPERIMENT_IMPRESSIONS=500
SEO_MIN_EXPERIMENT_CLICKS=20
SEO_MIN_EXPERIMENT_CONVERSIONS=3
SEO_KEYWORD_MAX_REPETITIONS=2
OPPORTUNITY_PROFIT_CONFIDENCE_THRESHOLD=65
OPPORTUNITY_MEDIA_COST_PER_CONTENT=0.03
OPPORTUNITY_INFRA_COST_PER_CONTENT=0.10
```

The initial niche, categories, problems, boards, keywords, and opportunity
weights are data configuration. Replace the taxonomy file to launch a new niche
without rewriting scoring logic.

## Demo mode

Demo mode demonstrates discovery → products → keyword research → ranking → brief
→ content → publication → impressions/clicks/conversions → revenue/cost/profit →
learning. Its products intentionally include high-SEO/weak-economics,
high-economics/weak-SEO, large-discount/poor-conversion, modest-discount/strong-
conversion, high-impression/poor-profit, and moderate-impression/high-profit
cases.

Demo prices, affiliate programs, trend values, policy states, and performance are
simulations. They prove workflow behavior, not market opportunity.

## Production credentials and real-world requirements

Required for reliable production operation:

- Pinterest business access token, approved app permissions, board IDs, analytics
  access, and conversion/import data.
- OpenAI API key only when AI creative refinement is enabled; demo generation is
  deterministic.
- One or more approved affiliate-network/merchant accounts, API/feed credentials,
  tracking IDs, official terms, and confirmed Pinterest/social/media rights.
- Authorized product feed/API with current price, inventory, images, and stable
  product identifiers.
- Conversion, reversal, cancellation, cost, and payout imports for true profit.

No ranking system can reliably estimate profit before accumulating sufficient
attributed impressions, clicks, conversions, reversals, and cost observations.
Until then, use confidence-aware score ranking and small allocations.

## Validation commands

```bash
.venv/bin/python -m pytest -q
.venv/bin/ruff check apps workers tests
.venv/bin/mypy apps workers
npm run lint:web
npm run typecheck:web
npm run test:web
npm run build:web
.venv/bin/alembic check
.venv/bin/pip-audit --skip-editable
npm audit --audit-level=high
```

Focused details remain in:

- `docs/PINTEREST_SEO.md`
- `docs/AFFILIATE_DISCOVERY.md`
- `docs/PRODUCT_DISCOVERY.md`
- `docs/OPPORTUNITY_SCORING.md`
- `docs/SEO_EXPERIMENTATION.md`
