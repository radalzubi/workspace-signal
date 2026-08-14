import Link from "next/link";
import { money, percent } from "@/lib/api";

type Metrics = { posts: number; impressions: number; clicks: number; ctr: number; conversions: number; conversion_rate: number; affiliate_revenue: number; ai_cost: number; operating_cost: number; advertising_spend: number; gross_profit: number; roas: number; profit_per_post: number; revenue_per_1000_impressions: number };
export type OverviewData = { today: Metrics; days_7: Metrics; days_30: Metrics; lifetime: Metrics; top_templates: {template: string; posts: number}[]; top_hooks: {hook: string; variants: number}[] };

export function Overview({ data, deals, health }: { data: OverviewData; deals: Array<Record<string, unknown>>; health: Record<string, unknown> }) {
  const m = data.days_30;
  const cards = [
    ["Gross profit", money(m.gross_profit), "Net of tracked costs", "profit"],
    ["Affiliate revenue", money(m.affiliate_revenue), `${m.conversions} conversions`, "revenue"],
    ["Outbound CTR", percent(m.ctr), `${m.clicks.toLocaleString()} clicks`, "ctr"],
    ["RPM", money(m.revenue_per_1000_impressions), "Per 1,000 impressions", "rpm"],
  ];
  return <>
    <div className="mode-banner"><div><b>Demo portfolio is running</b><p>Realistic products, price history, content, publications and attributed revenue are seeded.</p></div><Link className="primary" href="/content-queue">Review content queue →</Link></div>
    <div className="metrics">{cards.map(([label, value, note, cls]) => <article className={`metric ${cls}`} key={label}><p>{label}</p><strong>{value}</strong><small>{note}</small></article>)}</div>
    <div className="grid-main">
      <section className="panel"><div className="panel-head"><div><p className="eyebrow">ECONOMIC SIGNAL</p><h2>Profit funnel</h2></div><span className="pill">Last 30 days</span></div>
        <div className="funnel"><div><b>{m.impressions.toLocaleString()}</b><span>Impressions</span></div><i>→</i><div><b>{m.clicks}</b><span>Clicks</span></div><i>→</i><div><b>{m.conversions}</b><span>Purchases</span></div><i>→</i><div className="funnel-profit"><b>{money(m.gross_profit)}</b><span>Profit</span></div></div>
        <div className="chart" aria-label="Revenue chart"><div style={{height:"38%"}}/><div style={{height:"52%"}}/><div style={{height:"44%"}}/><div style={{height:"66%"}}/><div style={{height:"58%"}}/><div style={{height:"78%"}}/><div style={{height:"92%"}}/></div>
      </section>
      <section className="panel"><div className="panel-head"><div><p className="eyebrow">OPERATIONS</p><h2>System pulse</h2></div><span className="live-dot">LIVE</span></div>
        <dl className="health-list"><div><dt>Queue ready</dt><dd>{String(health.queue_length ?? 0)}</dd></div><div><dt>Failed jobs</dt><dd>{String(health.failed_jobs ?? 0)}</dd></div><div><dt>AI spend today</dt><dd>{money(Number(health.daily_ai_spend ?? 0))}</dd></div><div><dt>Ad spend today</dt><dd>{money(Number(health.daily_ad_spend ?? 0))}</dd></div></dl>
      </section>
    </div>
    <section className="panel"><div className="panel-head"><div><p className="eyebrow">OPPORTUNITY QUEUE</p><h2>Highest-value deals</h2></div><Link href="/deals">View all →</Link></div>
      <div className="table"><div className="tr th"><span>Product</span><span>Price</span><span>Discount</span><span>Score</span><span>Expected profit / 1K</span></div>{deals.slice(0,4).map((deal) => { const product = deal.product as Record<string, unknown>; return <div className="tr" key={String(deal.id)}><span><b>{String(product.product_name)}</b><small>{String(product.category)}</small></span><span>{money(String(product.current_price))}</span><span className="positive">−{String(product.discount_percent)}%</span><span><em className="score">{String(deal.deal_score)}</em></span><span>{money(String(deal.expected_profit_per_1000))}</span></div>})}</div>
    </section>
  </>;
}
