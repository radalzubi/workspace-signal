# Deployment

## Workspace Signal public-site launch

`workspacesignal.com` is the public publication. The Next.js app serves the
homepage, guide library, legal pages, sitemap, and robots policy as static or
statically generated pages. DealForge remains under operational routes such as
`/overview` and is protected by HTTP Basic authentication in production.

Before connecting the domain:

1. Create `hello@workspacesignal.com` and verify that it can receive mail.
2. Deploy `apps/web` to a Next.js-compatible host. Do not deploy the API publicly
   merely to launch the editorial site.
3. Configure strong, unique `DASHBOARD_USER` and `DASHBOARD_PASSWORD` secrets in
   the hosting provider. If they are absent, operational routes fail closed with
   HTTP 503 in production.
4. Add both `workspacesignal.com` and `www.workspacesignal.com` to the hosting
   project. Make the apex domain canonical.
5. In Namecheap Advanced DNS, add only the records shown by the selected host.
   Remove parking or redirect records that conflict with those values. Do not
   copy DNS values from an unrelated tutorial.
6. Wait for DNS and managed TLS validation, then verify `/`, `/guides`,
   `/privacy`, `/affiliate-disclosure`, `/robots.txt`, and `/sitemap.xml` over
   HTTPS.
7. Confirm `/overview` returns an authentication challenge and cannot be indexed.

Do not expose the FastAPI service until its production network boundary,
authentication, database, Redis, backups, and secrets have been configured.

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
