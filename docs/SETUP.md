# Setup

## Demo

Run `docker compose up --build`, visit <http://localhost:3000>, and use the
Content Queue to inspect generated media and dry-run publications. The demo admin
token is wired internally; do not expose the demo stack publicly.

## Production configuration

Copy `.env.example` to `.env`. Replace database/admin/anonymization secrets first.
Then set the niche, country, price/discount filters, time zone, posting windows,
and budget limits. Configuration validation refuses inverted price/post ranges or
enabled ads without positive hard budgets.

Set `DEMO_MODE=false` only after adding a legal product source. `CSVProductProvider`
and `JSONProductProvider` require the normalized fields documented in
`apps/api/schemas.py`; imports are size-limited and schema validated.

Never paste secret values into the onboarding wizard. Provider secrets belong in
environment variables, a deployment secret store, or the encrypted OAuth flow.

## First live checklist

- Domain and HTTPS are working.
- Database migrations and backups are tested.
- Product feed terms permit the intended use.
- Every asset has affirmative use authorization.
- Affiliate links and disclosures match program rules.
- Pinterest app access, scopes, redirect URI, board, and sandbox behavior pass.
- `DRY_RUN=true`, `AUTO_PUBLISH=false`, and `ENABLE_PAID_ADS=false` remain set.
- At least 20 queue items are manually inspected before changing any safety flag.

