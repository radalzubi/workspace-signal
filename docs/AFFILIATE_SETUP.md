# Affiliate setup

Choose a program that supplies a permitted product feed/API and permits social and
redirect usage. Obtain the tracking ID, feed/API credentials, cookie/attribution
window, commission schedule, prohibited-traffic rules, asset authorization, exact
disclosure text, and direct-link/redirect restrictions.

The generic link provider preserves the merchant URL and adds transparent UTM and
content IDs. Replace it with a provider adapter when the program requires a named
tag parameter or signed URL. Set `direct_link_required=true` when first-party
redirects are prohibited.

Every content item must map to one affiliate link. `/go/{slug}` stores only the
link/content/campaign, referrer where available, UTM fields, timestamp, and a
daily salted visitor hash, then returns a no-store 302 redirect.

CSV conversion imports require:

```text
external_id,converted_at,order_value,commission,currency
```

Optional attribution columns are `product_id`, `content_id`, and `campaign`.
Imports are idempotent by provider plus external ID.

Never cloak a destination or remove required disclosure. The default copy is:
“Affiliate link — I may earn a commission from qualifying purchases.” Replace it
with the exact program/platform requirement where necessary.

For the current real-product launch sequence, verified product records, the
Anker application copy, a permission email, and activation gates, see
[Real product launch](REAL_PRODUCT_LAUNCH.md).
