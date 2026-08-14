import { money, percent } from "@/lib/api";

export type Opportunity = {
  id: string;
  product: string;
  category: string;
  merchant: string;
  current_price: number;
  average_30d: number | null;
  observed_low: number | null;
  discount_percent: number;
  affiliate_program: string;
  commission_rate: number;
  estimated_commission_per_sale: number;
  search_intent_score: number;
  seo_opportunity: number;
  expected_impressions: number;
  expected_ctr: number;
  expected_conversion_rate: number;
  expected_epc: number;
  expected_profit_per_1000: number;
  expected_profit_low: number;
  expected_profit_high: number;
  opportunity_score: number;
  confidence: number;
  rank_basis: string;
  price_band: string;
  discount_band: string;
  saturation_penalty: number;
  risk_penalty: number;
  recommended_content_angle: string;
  recommended_keyword_cluster: string | null;
  recommended_board: string | null;
  selection_reason: string;
  score_breakdown: Record<string, unknown>;
};

export function OpportunityFeed({ opportunities }: { opportunities: Opportunity[] }) {
  const expectedProfit = opportunities.reduce((sum, item) => sum + item.expected_profit_per_1000, 0);
  const profitRanked = opportunities.filter((item) => item.rank_basis === "expected_profit").length;
  return <>
    <div className="metrics">
      <article className="metric profit"><p>Modeled profit / 1K</p><strong>{money(expectedProfit)}</strong><small>Across current opportunities</small></article>
      <article className="metric revenue"><p>Profit-ranked</p><strong>{profitRanked}</strong><small>Confidence threshold cleared</small></article>
      <article className="metric ctr"><p>Products scored</p><strong>{opportunities.length}</strong><small>Current active deals</small></article>
      <article className="metric rpm"><p>Optimization target</p><strong>Profit</strong><small>Views are diagnostic only</small></article>
    </div>
    <section className="panel">
      <div className="panel-head"><div><p className="eyebrow">CAPITAL-ALLOCATION VIEW</p><h2>Top opportunities today</h2></div><span className="pill">CONFIDENCE-AWARE</span></div>
      <div className="opportunity-grid">
        {opportunities.map((item, index) => <article className="opportunity-card" key={item.id}>
          <div className="opportunity-rank">#{index + 1}</div>
          <div className="opportunity-title"><div><b>{item.product}</b><small>{item.merchant} · {item.category}</small></div><em className="score">{item.opportunity_score.toFixed(0)}</em></div>
          <div className="opportunity-economics"><div><span>Expected profit / 1K</span><b>{money(item.expected_profit_per_1000)}</b><small>{money(item.expected_profit_low)}–{money(item.expected_profit_high)}</small></div><div><span>Expected EPC</span><b>{money(item.expected_epc)}</b><small>{percent(item.expected_conversion_rate)} conversion</small></div><div><span>Commission / sale</span><b>{money(item.estimated_commission_per_sale)}</b><small>{percent(item.commission_rate)} rate</small></div></div>
          <dl className="opportunity-detail"><div><dt>Price signal</dt><dd>{money(item.current_price)} · {item.discount_band}</dd></div><div><dt>Keyword cluster</dt><dd>{item.recommended_keyword_cluster ?? "Research needed"}</dd></div><div><dt>Board</dt><dd>{item.recommended_board ?? "Unassigned"}</dd></div><div><dt>Ranking basis</dt><dd>{item.rank_basis.replaceAll("_", " ")} · {item.confidence.toFixed(0)}% confidence</dd></div></dl>
          <p className="reason">{item.selection_reason}</p>
          <div className="risk-row"><span>SEO {Number(item.seo_opportunity ?? 0).toFixed(0)}</span><span>Saturation −{item.saturation_penalty.toFixed(0)}</span><span>Risk −{item.risk_penalty.toFixed(0)}</span></div>
        </article>)}
      </div>
    </section>
  </>;
}
