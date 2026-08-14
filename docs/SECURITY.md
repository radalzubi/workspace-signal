# Security

## Implemented controls

- Environment-only secrets, encrypted OAuth token storage, `.env` exclusion, and
  no client-side admin credential.
- Bearer protection for mutations, strict input schemas, import size/type limits,
  restricted CORS, request IDs, structured logs, and security headers.
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

## Privacy notice baseline

Disclose affiliate relationships, outbound-click recording, purpose, retention,
cookie behavior, processors, user rights, and contact details. The included
redirect does not set cookies, but hosting/CDN logs may still process IP addresses.
Obtain jurisdiction-specific legal review before public launch.

Report suspected credential exposure by revoking the credential first, then
removing it from history and investigating logs.

