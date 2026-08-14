# Affiliate-program discovery

DealForge stores structured research about potential affiliate programs and
scores expected value rather than headline commission percentage.

## Implemented

- JSON research-directory adapter with Pydantic validation and a 5 MB limit.
- Idempotent program upsert by network, program name, and country.
- Status and approval workflows that distinguish discovery from approval.
- Risk-adjusted attractiveness scoring.
- Score history, version, component evidence, and confidence.
- Discovery-source capability catalog.
- Dashboard comparison of economics, feeds/APIs, policy status, media rights,
  reporting, and unresolved risks.

The bundled entries are explicitly fictional demo programs. They are not real
offers and must never be used as program terms.

## Not implemented or automated

DealForge does not submit applications, accept contracts, provide business
identity, or assume eligibility. Network adapters are documented boundaries,
not mocked live integrations. A row marked `approved` is only authoritative when
confirmed by the operator from the actual account.

Potential adapter sources include:

- [impact.com Partner integrations](https://integrations.impact.com/impact-publisher)
- [Awin publisher APIs and feeds](https://help.awin.com/apidocs/for-publishers)
- [CJ publisher/API paths](https://docs.cj.com/docs/finding-your-path)
- [Amazon Creators API prerequisites](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction)

Each requires its own account, approval, credentials, terms review, and often a
merchant relationship. Amazon’s current documentation, for example, states
marketplace enrollment, qualifying sales, API registration, and credentials as
prerequisites; DealForge does not bypass them.

## Program score

The deterministic score considers commission value, expected conversion rate,
average order value, feed/API/deep-link quality, content/category fit, Pinterest
permission, reporting quality, merchant reputation, cookie duration, return
risk, media rights, approval, and availability.

Expected revenue per 100 clicks is:

```text
100 × conversion rate × average order value × commission rate
```

Unknown Pinterest permission, unknown media rights, missing approval, paused
status, and return risk reduce the score. Unknown fields reduce confidence.

Before enabling a program, verify its official page, social/Pinterest rules,
redirect rules, media license, current commission groups, reversals, geography,
tax/payment requirements, and reporting identifiers. Record `terms_last_checked`
and retain the official source URL.
