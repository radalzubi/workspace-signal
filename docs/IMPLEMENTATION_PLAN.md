# DealForge MVP implementation plan

## Product decision

Build a Pinterest-first affiliate deal operating system that is useful with no
credentials and becomes live by swapping provider configuration. The first
recommended niche is **small-space desk setup deals**: it has visual purchase
intent, evergreen discovery behavior, broad price bands, and repeatable bundles.

## Architecture

- `apps/api`: FastAPI API, SQLAlchemy domain model, provider adapters, redirect
  tracking, analytics, onboarding, and admin actions.
- `apps/web`: Next.js TypeScript admin dashboard.
- `workers`: Celery tasks and schedule for ingestion, publication, revalidation,
  analytics simulation, and daily optimization.
- `templates`: data-driven content templates.
- `media`: generated media in development; an S3-compatible storage adapter is
  used in production.
- `infrastructure`: container and deployment configuration.
- `scripts`: backup, restore, and operational scripts.
- `tests`: deterministic tests for commercial and safety-critical behavior.

PostgreSQL and Redis are the production-shaped defaults. SQLite is supported for
fast tests and a zero-credential local demo. External services are isolated
behind typed provider interfaces.

## Phase gates

### Phase 1 — commercial data core

- Product/merchant/price schema and migrations.
- Generic provider protocol plus mock, CSV, and JSON ingestion.
- Rolling price intelligence with honest “observed low” language.
- Explainable 0–100 deal scoring and expected-profit estimate.
- Demo data bootstrap and tests.

Acceptance: demo products and histories persist; price statistics and score
explanations are deterministic; Phase 1 tests pass.

### Phase 2 — content system

- Deterministic provider plus OpenAI Responses API structured-output adapter.
- Configurable template library, similarity guard, claim policy, disclosures.
- Static Pin rendering and FFmpeg vertical-video rendering.
- Licensing metadata and approval queue.

Acceptance: demo mode produces previewable content without credentials; unsafe,
duplicate, stale, or incomplete content cannot enter the publish path.

### Phase 3 — distribution and attribution

- Affiliate-link builder and optional `/go/{slug}` first-party redirect.
- Pinterest API v5 OAuth, board discovery, image/video publication, retries,
  idempotency, and dry-run behavior.
- Export-only adapters for Instagram, TikTok, and YouTube Shorts.
- Cadence-aware application scheduler.

Acceptance: dry-run publication is complete; a live call is impossible unless
explicit configuration and credentials are valid.

### Phase 4 — economics dashboard

- Performance, conversion, revenue, and cost models and imports.
- Today/7d/30d/lifetime metrics and health telemetry.
- Unit-economics scenario calculator.
- Daily/monthly AI budget enforcement.

Acceptance: dashboard reflects seeded funnel and profit; CSV conversion import
maps attribution when identifiers exist.

### Phase 5 — learning loop

- Experiment variants, winner lifecycle, daily strategy snapshot.
- Bounded scoring-weight changes with history and rollback records.

Acceptance: recommendations cite observed metrics and no LLM can directly mutate
production scoring code or budgets.

### Phase 6 — paid promotion safeguards

- Provider interface and manual spend import.
- Default-off eligibility gate requiring explicit enablement, configured hard
  budgets, and winner-level organic evidence.

Acceptance: tests prove spend is rejected on every missing prerequisite.

### Phase 7 — hardening and handoff

- Authentication, input/rate limits, safe media handling, structured logging,
  health/readiness, backups, dependency scanning, CI, and deployment docs.
- Full backend tests, frontend lint/type/build, migration validation, and Docker
  configuration validation.

Acceptance: documented one-command demo, production checklist, credentials list,
known limitations, cost estimate, and clean local Git history.

## Explicit non-goals for the MVP

- Retail scraping, unofficial login automation, fake engagement, and prohibited
  link cloaking.
- Autonomous real-money advertising or unreviewed auto-publishing.
- Claims based on invented reviews, personal use, or unsupported price history.
- Generative video as a base dependency; the renderer uses licensed product
  assets, text, transitions, and optional cached voiceover.

## Delivery risks and controls

- Provider approval: all integrations have deterministic dry-run fallbacks.
- Stale deals: revalidate immediately before publish and flag material changes.
- Platform policy changes: API paths/scopes are configurable and documented with
  current official source links and a verification date.
- Margin illusion: optimize attributable profit, record AI/infrastructure/ad
  costs, and distinguish estimates from imported actuals.
- Account spam risk: daily limits, posting windows, similarity checks, approval
  mode by default, and template-fatigue penalties.
