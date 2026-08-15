# Security

## Implemented controls

- Environment-only secrets, encrypted OAuth token storage, `.env` exclusion, and
  no client-side admin credential.
- Bearer protection for all operational reads and mutations. Only health/readiness,
  the signed Pinterest OAuth callback, and anonymized affiliate redirects are public.
- Strict input schemas, a 5 MiB request/upload ceiling, path validation, upstream
  timeouts, restricted CORS and trusted hosts, request IDs, and structured logs.
- Browser defenses include a restrictive Content Security Policy, HSTS, clickjacking,
  MIME-sniffing, referrer, permissions, opener, and crawler controls. The private
  dashboard fails closed when strong credentials are absent and is never cached or indexed.
- Production startup rejects placeholder/short master secrets and wildcard origin or
  host policies. Production API documentation and schema endpoints are disabled.
- Daily salted visitor hashes; no raw IP persistence or unnecessary identity data.
- Safe local-path containment, no shell interpolation, bounded FFmpeg timeout, and
  HTTP timeouts/retries.
- Idempotent publications, database uniqueness constraints, hard AI/ad budgets,
  and default-off external mutations.
- CI dependency audit, secret scan, lint/type/test/build, and migration validation.

## Production checklist

- Generate independent 32+ character secrets. Never reuse the database password,
  admin key, anonymization salt, or storage key.
- Use HTTPS, private database/Redis networking, a WAF/gateway limiter, restricted
  outbound network rules, non-root containers, and least-privilege IAM.
- Replace master-secret encryption with KMS/envelope encryption at multi-user or
  regulated scale. Rotate Pinterest/affiliate/API keys and test revocation.
- Add operator identity/SSO and audit logs before giving multiple people access.
- Run `pip-audit`, `npm audit`, image scanning, and GitHub secret scanning on every
  release. Patch critical vulnerabilities before deployment.
- Back up encrypted data separately from its decryption key.

## Operating requirements

- Enable MFA on GitHub, Vercel, Namecheap, Pinterest, email, and every affiliate network.
- Store production secrets only in the deployment provider's encrypted environment
  settings. Never prefix a secret with `NEXT_PUBLIC_` or commit `.env` files.
- Keep the API private behind the authenticated web proxy where possible. If it is
  internet-facing, put it behind a WAF and distributed rate limiter; the built-in
  limiter intentionally covers only one process.
- Rotate the Pinterest app secret, admin key, database credentials, and email password
  immediately if they are pasted into chat, screenshots, logs, or source control.
- Review operator access quarterly and remove unused credentials, apps, and collaborators.

No website can be guaranteed "unhackable." These controls materially reduce the attack
surface, fail closed when secrets are missing, and make compromise less likely and less
damaging; continuous patching, MFA, monitoring, backups, and credential rotation remain required.

## Privacy notice baseline

Disclose affiliate relationships, outbound-click recording, purpose, retention,
cookie behavior, processors, user rights, and contact details. The included
redirect does not set cookies, but hosting/CDN logs may still process IP addresses.
Obtain jurisdiction-specific legal review before public launch.

Report suspected credential exposure by revoking the credential first, then
removing it from history and investigating logs.
