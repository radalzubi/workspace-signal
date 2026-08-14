import { money } from "@/lib/api";

type Report = { period: string; optimization_target: string; insights: string[]; recommendations: string[]; minimum_sample_guard: { observed_impressions: number; observed_conversions: number; decision_ready: boolean }; evidence: { price_bands: Array<{ label: string; profit_per_1000_impressions: number }>; discount_bands: Array<{ label: string; profit_per_1000_impressions: number }> }; generated_deterministically: boolean };

export function StrategyReport({ report }: { report: Report }) {
  return <>
    <div className="mode-banner"><div><b>Optimization target: {report.optimization_target.replaceAll("_", " ")}</b><p>Recommendations summarize attributed evidence; they cannot rewrite ranking weights or budgets.</p></div><span className="pill">{report.minimum_sample_guard.decision_ready ? "DECISION READY" : "SAMPLE GUARD ACTIVE"}</span></div>
    <div className="grid-main"><section className="panel"><div className="panel-head"><div><p className="eyebrow">OBSERVED EVIDENCE</p><h2>Weekly search strategy</h2></div></div><ol className="insight-list">{report.insights.map((item) => <li key={item}>{item}</li>)}</ol></section><section className="panel"><div className="panel-head"><div><p className="eyebrow">SAMPLE HEALTH</p><h2>Decision guard</h2></div></div><dl className="health-list"><div><dt>Attributed impressions</dt><dd>{report.minimum_sample_guard.observed_impressions.toLocaleString()}</dd></div><div><dt>Attributed conversions</dt><dd>{report.minimum_sample_guard.observed_conversions}</dd></div><div><dt>Weight change ready</dt><dd>{report.minimum_sample_guard.decision_ready ? "Yes" : "No"}</dd></div><div><dt>Report method</dt><dd>{report.generated_deterministically ? "Deterministic" : "AI summary"}</dd></div></dl></section></div>
    <section className="panel"><div className="panel-head"><div><p className="eyebrow">BOUNDED ACTIONS</p><h2>Recommended changes</h2></div></div><div className="recommendation-grid">{report.recommendations.map((item) => <article key={item}>{item}</article>)}</div></section>
    <div className="grid-main"><Band title="Price bands" rows={report.evidence.price_bands}/><Band title="Discount bands" rows={report.evidence.discount_bands}/></div>
  </>;
}

function Band({ title, rows }: { title: string; rows: Array<{ label: string; profit_per_1000_impressions: number }> }) { return <section className="panel"><div className="panel-head"><div><p className="eyebrow">PROFIT LEARNING</p><h2>{title}</h2></div></div><div className="comparison-stack">{rows.map((row) => <article key={row.label}><div><b>{row.label}</b></div><strong>{money(row.profit_per_1000_impressions)}<small>profit / 1K</small></strong></article>)}</div></section>; }
