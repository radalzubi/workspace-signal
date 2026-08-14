# Content pipeline

## Strategy

The deterministic provider works without credentials. The OpenAI adapter uses the
Responses API with SDK-native Pydantic structured output. It supplies only factual
name, brand, category, description, listed price, observed price statistics,
availability, and disclosure. Inputs/outputs and estimated cost are recorded.

The implementation follows the current [official OpenAI Structured Outputs
guide](https://developers.openai.com/api/docs/guides/structured-outputs), verified
2026-08-14. If daily/monthly AI budgets are reached, optional AI generation falls
back to deterministic content rather than breaking critical workflows.

## Templates and media

`templates/content_templates.json` controls hooks, labels, and accents. Add a
template without changing the scoring or provider layer. The initial library is
`deal_alert`, `under_50`, `price_drop`, `problem_solution`, and `small_space`.

Pillow renders original 1000×1500 Pins. FFmpeg turns a Pin into a 1080×1920,
25-second vertical video with safe argument handling, fades, and subtle motion.
No social-platform music or unauthorized retailer image is downloaded. When
authorized product assets are introduced, create an `Asset` row with source,
license, authorization, retrieval date, and checksum before rendering.

## Quality gate

Publication is blocked for missing/rendering-failed media, prohibited claims,
missing disclosure, missing/broken link, unavailable product, stale price, expired
deal, or caption length violation. Similarity checks deter repeated spam. Deals
must be revalidated at publication time.

Never produce personal-use testimony or unsupported “best/guaranteed/lowest ever”
claims. Prefer “Based on listed specifications,” “Current listed price,” and
“Lowest price observed by our system.”

