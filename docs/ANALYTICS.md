# Analytics and attribution

The dashboard exposes today, 7-day, 30-day, and lifetime posts, impressions,
clicks, CTR, conversions, conversion rate, affiliate revenue, AI/operating/ad
costs, gross profit, ROAS, profit per post, earnings per click, and revenue per
1,000 impressions.

Pinterest organic analytics can be added through the official Pin analytics
endpoints after app access. Pinterest currently documents a 90-day lookback,
lifetime reporting for most Pins, and batch analytics for up to 100 Pin IDs; see
[Organic reporting](https://developers.pinterest.com/docs/analytics-and-reports/organic-reporting/).

Attribution priority is exact content ID, then campaign, then product. Never claim
precision unavailable from the affiliate program. Distinguish API-imported actual
revenue from projections and manual inputs.

The unit-economics calculator models impressions → clicks → conversions →
commission revenue, subtracts advertising/AI/infrastructure costs, and returns
gross profit, cost per conversion, break-even CPC/CPM, ROAS, and profit margin.

Daily strategy snapshots retain evidence and scoring weights. Weight shifts are
recommendations only, limited to 5% until enough conversion data supports a
proper model. Upgrade to a contextual bandit after several hundred conversions,
stable attribution, and guardrail monitoring—not merely after high view counts.

