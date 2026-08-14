# Architecture

## System boundaries

The FastAPI service is the source of truth for products, price observations,
deals, content, approvals, publications, attribution, conversions, costs, and
strategy. Next.js is an operator surface; Celery performs idempotent scheduled
work; PostgreSQL persists state; Redis brokers jobs; media is local in development
and S3-compatible in production.

Provider protocols isolate product ingestion, AI, TTS, storage, social publishing,
conversion import, alerting, and paid promotion. This prevents any niche,
retailer, model vendor, or platform from becoming a core dependency.

## Critical sequence

1. Provider observations upsert normalized products and append prices.
2. Price intelligence calculates 7/30/90-day averages and observed lows.
3. Heuristic scoring produces an explainable score and expected profit per 1,000
   impressions. Historical models can replace this implementation later.
4. AI/mock strategy receives only factual product context and emits a validated
   `ContentStrategy` schema.
5. Templates and renderer create media. Assets record source, license,
   authorization, retrieval date, and checksum.
6. Affiliate links and disclosure are attached. Quality gates check claims,
   duplication, media, disclosure, link, stock, price age, and expiration.
7. Approval/scheduler sends eligible content through an idempotent publisher.
8. Clicks and imported conversions reconcile against content and campaign IDs.
9. Daily strategy snapshots analyze outcomes and recommend bounded changes. LLMs
   cannot rewrite algorithms, budgets, or production settings.

## Security decisions

- Browser mutations use a Next.js server proxy; the admin bearer token remains
  server-only. Bearer auth avoids cookie CSRF exposure.
- OAuth tokens are encrypted before persistence using a key derived from the
  deployment master secret. Use a managed secret/KMS system at larger scale.
- Redirect visitor IDs are daily salted hashes, not raw IP storage.
- FFmpeg receives an argument array and validated local path; no untrusted shell
  interpolation exists.
- Decimal/Numeric types represent money. Timestamps are UTC and timezone-aware.
- Publication uniqueness is enforced by platform plus idempotency key.

## Scaling path

Scale API and worker replicas independently, move rate limiting to Redis/gateway,
use managed PostgreSQL with PITR, send media to object storage/CDN, and route
structured logs/errors to an observability vendor. Split analytics into a
warehouse only after operational Postgres queries become material load.

