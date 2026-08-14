# Pinterest integration

Verified against official Pinterest documentation on 2026-08-14.

## Account and app access

Create/convert a Pinterest business account, verify its email, register a developer
app, submit for Trial access, and configure the OAuth redirect URI exactly. Trial
Pins may only be visible to the creator; Standard access is required for normal
production distribution.

The implementation uses Authorization Code OAuth with CSRF state, the token
endpoint at `/v5/oauth/token`, and least-required scopes:

```text
boards:read boards:write pins:read pins:write
```

Start connection through `GET /api/v1/integrations/pinterest/connect` with the
admin bearer token. The callback exchanges the code and stores tokens encrypted;
the browser never receives secret values. Configure `PINTEREST_BOARD_ID` after
calling the protected board-discovery endpoint.

Image publication calls `POST /v5/pins` with a title (100 characters maximum),
description (800 maximum), outbound link, alt text, board ID, and base64 image.
429/timeouts/5xx receive bounded exponential-backoff retries. A platform/content
idempotency key prevents duplicate Pins.

Video media generation is included. Live video upload remains export-ready in the
MVP because Pinterest’s official flow is a separate media registration and AWS
multipart upload; validate it against the approved app before enabling.

Official sources:

- [Authentication and authorization](https://developers.pinterest.com/docs/getting-started/set-up-authentication-and-authorization/)
- [Create a Pin API](https://developers.pinterest.com/docs/api/v5/pins-create/)
- [Boards and Pins guide](https://developers.pinterest.com/docs/work-with-organic-content-and-users/create-boards-and-pins/)
- [Sandbox](https://developers.pinterest.com/docs/developer-tools/sandbox/)
- [Access tiers](https://developers.pinterest.com/docs/key-concepts/access-tiers/)
- [Rate limits](https://developers.pinterest.com/docs/reference/rate-limits/)

