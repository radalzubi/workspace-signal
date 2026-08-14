# Deployment

## Lean architecture

For an early single-founder operation, use one 2–4 vCPU Linux VPS for Docker
Compose, plus offsite database/media backups. Put a CDN/WAF in front of web/API
and use an S3-compatible bucket for production media. A shared VPS is suitable for
moderate traffic; move PostgreSQL to managed HA/PITR before revenue dependence.

Approximate early requirements: 2–4 vCPU, 4–8 GB RAM, 40+ GB SSD, and 10–30 GB
monthly media. The Docker stack contains web, API, worker, scheduler, PostgreSQL,
and Redis. Keep ports 5432/6379 private.

## Procedure

1. Provision Ubuntu/Debian, Docker Engine/Compose, DNS, HTTPS reverse proxy, and a
   firewall allowing only 22 (restricted), 80, and 443.
2. Copy the repository and `.env`; set production secrets, domain URLs, allowed
   origin, Postgres password, and object storage.
3. Run `docker compose build`, `docker compose run --rm api alembic upgrade head`,
   and `docker compose up -d`.
4. Verify `/api/v1/health`, `/api/v1/ready`, `/overview`, worker heartbeats, media,
   redirect behavior, and backups.
5. Keep dry-run/manual approval flags until the launch checklist passes.

Cloudflare R2 is S3-compatible and, as of 2026-08-14, documents a 10 GB-month
standard-storage free allowance, $0.015/GB-month thereafter, and free direct
egress. Verify [current R2 pricing](https://developers.cloudflare.com/r2/pricing/)
before purchase. A shared Hetzner VPS starts in the single-digit monthly range,
but plan availability, region, VAT, and IP charges vary; verify [current cloud
plans](https://www.hetzner.com/cloud/).

## Production checklist

- `ENVIRONMENT=production`, `DEMO_MODE=false`, strong secrets, HTTPS URLs.
- Database/Redis private; volumes encrypted; backup/restore drill completed.
- WAF/rate limit, monitoring, alert routing, log retention, and clock synchronization.
- Pinterest/affiliate terms and credentials validated; disclosures reviewed.
- AI/ad budgets and invoice alerts set at both application and vendor levels.
- Container images pinned/scanned; CI green; migration rollback understood.

