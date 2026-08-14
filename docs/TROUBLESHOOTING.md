# Troubleshooting

## Dashboard cannot reach API

Check `docker compose ps`, API health, `API_INTERNAL_URL=http://api:8000` inside the
web container, and `NEXT_PUBLIC_API_URL` as the browser-reachable HTTPS/API URL.
CORS must exactly include the dashboard origin.

## Demo is empty

Inspect API logs for `demo_bootstrap_failed`. Confirm the migration applied and
the media volume is writable. Trigger `POST /api/v1/pipeline/run` through the
authenticated dashboard proxy. Demo bootstrap is idempotent.

## Media missing / video absent

Check `MEDIA_ROOT`, write permissions, DejaVu fonts, and `ffmpeg -version`. Static
Pins still render if FFmpeg is unavailable; Docker installs both dependencies.
Never loosen path validation to work around an error.

## Content is blocked

Read `quality_report.errors`. Refresh product/price data, restore authorized media,
fix disclosure/link/caption, or reject/regenerate. Do not bypass the gate.

## Pinterest 401/403

Confirm app approval/tier, token expiration, exact redirect URI, board ownership,
and scopes. Reconnect OAuth rather than copying tokens into code. Trial Pins may
have limited visibility.

## Pinterest 429/5xx

The adapter retries transient failures with bounded exponential backoff. Inspect
rate-limit headers and lower cadence. Idempotency prevents retry duplicates.

## Migration failure

Back up first. Run `alembic current`, `alembic history`, and inspect database logs.
Never edit an applied migration; create a corrective migration.

## Unexpected spend

Set `ENABLE_PAID_ADS=false`, revoke ad credentials, stop workers, and reconcile
manual/API cost rows. Application safeguards do not replace platform billing caps.

