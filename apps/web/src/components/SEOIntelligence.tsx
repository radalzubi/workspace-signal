import { money, percent } from "@/lib/api";

type Performance = { label: string; intent?: string; impressions: number; clicks: number; ctr: number; conversions: number; conversion_rate: number; revenue: number; profit: number; epc: number; profit_per_1000_impressions: number; confidence?: number };
type Taxonomy = { clusters: Array<{ id: string; name: string; type: string; intent: string; keyword_count: number }>; boards: Array<{ id: string; name: string; category: string; historical_profit_per_1000: number; historical_conversion_rate: number }> };
type Experiment = { id: string; name: string; hypothesis: string; arms: Array<{ label: string; keyword: string; impressions: number; conversions: number; profit: number }>; evaluation: { status: string; winner: string | null } };

export function SEOIntelligence({ analytics, taxonomy, experiments }: { analytics: { keywords: Performance[]; price_bands: Performance[]; discount_bands: Performance[]; content_types: Performance[] }; taxonomy: Taxonomy; experiments: Experiment[] }) {
  const measured = analytics.keywords.filter((row) => row.impressions > 0);
  const topProfit = measured[0];
  return <>
    <div className="section-intro"><div><p className="eyebrow">SEARCH → CLICK → PURCHASE → PROFIT</p><h2>Pinterest SEO intelligence</h2></div><span className="pill">HEURISTICS LABELED</span></div>
    <div className="metrics">
      <article className="metric profit"><p>Top keyword profit / 1K</p><strong>{money(topProfit?.profit_per_1000_impressions ?? 0)}</strong><small>{topProfit?.label ?? "Awaiting traffic"}</small></article>
      <article className="metric revenue"><p>Keywords measured</p><strong>{measured.length}</strong><small>With attributed impressions</small></article>
      <article className="metric ctr"><p>Semantic clusters</p><strong>{taxonomy.clusters.length}</strong><small>Coherent intent groups</small></article>
      <article className="metric rpm"><p>Board taxonomy</p><strong>{taxonomy.boards.length}</strong><small>One best-fit board per Pin</small></article>
    </div>
    <div className="grid-main">
      <section className="panel"><div className="panel-head"><div><p className="eyebrow">PROFIT ATTRIBUTION</p><h2>Keyword performance</h2></div><span className="pill">NOT IMPRESSIONS-ONLY</span></div><div className="seo-table"><div className="seo-row seo-head"><span>Keyword</span><span>Intent</span><span>Impr.</span><span>CTR</span><span>Conv.</span><span>EPC</span><span>Profit / 1K</span></div>{analytics.keywords.slice(0,12).map((row) => <div className="seo-row" key={row.label}><span><b>{row.label}</b></span><span>{row.intent?.replaceAll("_", " ")}</span><span>{row.impressions.toLocaleString()}</span><span>{percent(row.ctr)}</span><span>{row.conversions}</span><span>{money(row.epc)}</span><span className={row.profit >= 0 ? "positive" : "negative"}>{money(row.profit_per_1000_impressions)}</span></div>)}</div></section>
      <section className="panel"><div className="panel-head"><div><p className="eyebrow">CONTENT DURABILITY</p><h2>Evergreen vs deal</h2></div></div><div className="comparison-stack">{analytics.content_types.map((row) => <article key={row.label}><div><b>{row.label}</b><small>{row.impressions.toLocaleString()} impressions · {row.conversions} purchases</small></div><strong>{money(row.profit_per_1000_impressions)}<small>profit / 1K</small></strong></article>)}</div></section>
    </div>
    <div className="grid-main">
      <section className="panel"><div className="panel-head"><div><p className="eyebrow">SEMANTIC STRUCTURE</p><h2>Keyword clusters</h2></div></div><div className="chip-cloud">{taxonomy.clusters.map((cluster) => <span key={cluster.id}><b>{cluster.name}</b><small>{cluster.intent.replaceAll("_", " ")} · {cluster.keyword_count} terms</small></span>)}</div></section>
      <section className="panel"><div className="panel-head"><div><p className="eyebrow">EXPERIMENT GUARDRAILS</p><h2>Keyword tests</h2></div></div><div className="comparison-stack">{experiments.map((experiment) => <article key={experiment.id}><div><b>{experiment.name}</b><small>{experiment.evaluation.status.replaceAll("_", " ")}</small></div><strong>{experiment.evaluation.winner ?? "Collecting data"}<small>{experiment.arms.length} arms</small></strong></article>)}</div></section>
    </div>
    <section className="panel"><div className="panel-head"><div><p className="eyebrow">BOARD RELEVANCE</p><h2>Configured board taxonomy</h2></div></div><div className="generic-list">{taxonomy.boards.map((board) => <article key={board.id}><div><b>{board.name}</b><small>{board.category}</small></div><div><strong>{money(board.historical_profit_per_1000)}</strong><small>{percent(board.historical_conversion_rate)} conversion</small></div></article>)}</div></section>
  </>;
}
