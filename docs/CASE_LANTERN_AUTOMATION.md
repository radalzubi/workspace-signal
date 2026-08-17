# Case Lantern automation

Case Lantern is DealForge's human-approved TikTok story workflow. It is deliberately separate from the Workspace Signal affiliate workflow so the two brands, audiences, and analytics do not become mixed.

## Current operating mode

- Brand: `Case Lantern`
- Proposed handle: `@caselantern`
- Channel: TikTok
- Cadence: one draft brief per day
- Publishing mode: draft only
- Human approval: required and enforced
- Initial format: sourced historical true-crime and unexplained cases
- Initial pilot: the D. B. Cooper hijacking, grounded in two FBI sources

Setting `CASE_LANTERN_ENABLED=true` allows the scheduler to create and validate a daily brief. It does not publish a video. Public publishing stays locked even after a story passes automated checks.

## Workflow

1. A story project is created with a hook, original script, caption, content warning, and visual plan.
2. Every factual claim is linked to one or more stored sources.
3. Deterministic validation checks source count, official-source coverage, claim support, script length, risky wording, caption citations, and the safety-risk ceiling.
4. The operator reviews the evidence in the private `/case-lantern` dashboard.
5. The operator approves, rejects, or requests a rewrite.
6. Only an approved story can be exported as a versioned TikTok draft package.
7. A human performs the final platform review and publishes the finished video.

## What is deterministic

- source and claim relationships
- source-count and official-source checks
- word-count limits
- risky-language checks
- approval-state transitions
- the no-export-before-approval rule
- the no-public-auto-post rule
- audit timestamps and publication records

## What can use AI later

- suggesting public-record story candidates
- drafting original scripts from verified claims
- proposing hooks, captions, and visual beats
- narration and original visual generation

AI output must remain a draft. It may not introduce a fact that is absent from the structured claim set, identify an uncharged living person as guilty, imitate a real person's voice, or generate graphic imagery.

## API and dashboard

- `GET /api/v1/case-lantern/stories` lists projects and validation evidence.
- `POST /api/v1/case-lantern/pilot` creates the idempotent sourced pilot.
- `PATCH /api/v1/case-lantern/stories/{id}` accepts `approve`, `reject`, `regenerate`, or `export`.
- `/case-lantern` is private, dashboard-authenticated, and excluded from search indexing.

An export writes `media/generated/case-lantern/<story-slug>/tiktok-draft-package.json` and creates a `SocialPublication` audit record. The package is production input for a renderer/uploader; it is not itself a published TikTok.

## TikTok credentials and platform approval

No TikTok secret is required for research, validation, approval, or local export. Sending a draft to TikTok requires an approved TikTok developer app, OAuth credentials, the relevant Content Posting API scope, and a production HTTPS callback. Direct public posting requires the additional TikTok audit and remains disabled until that approval is confirmed.

Required secrets, when available:

```text
TIKTOK_CLIENT_KEY=
TIKTOK_CLIENT_SECRET=
TIKTOK_REDIRECT_URI=https://your-api.example.com/api/v1/integrations/tiktok/callback
```

Never commit those values. Store them only in the production secret manager.

## Starting the scheduler

The existing application stack runs the daily job through Celery Beat:

```bash
docker compose up -d --build
```

The API container applies Alembic migrations before starting. The `scheduler` service queues `workers.tasks.case_lantern_daily_brief`; the `worker` service executes it. Docker, PostgreSQL, and Redis must be available for this production-shaped local workflow.

## Editorial safety rules

- Prefer historical, closed, or official-public-record cases.
- Use at least two credible sources and at least one official source when available.
- Attribute disputed details and label uncertainty.
- Do not use gore, crime instructions, fabricated dialogue, copyrighted TV/podcast clips, or cloned voices.
- Do not accuse an uncharged living person.
- Include a clear source list and content warning when appropriate.
- Treat victim dignity and factual accuracy as release blockers.

## Definition of done for full automation

The current phase is complete through approved draft-package export. Full TikTok delivery is not complete until an original-media renderer, licensed narration provider, TikTok OAuth flow, and approved draft-upload integration have each passed their own tests and platform review. Public posting must remain a final human action unless TikTok explicitly grants and audits Direct Post access.
