import Link from "next/link";

const navigation = [
  ["overview", "Overview"], ["products", "Products"], ["deals", "Deals"],
  ["opportunities", "Opportunities"], ["seo", "SEO Intelligence"], ["affiliate-programs", "Affiliate Programs"],
  ["content", "Content"], ["content-queue", "Content Queue"], ["published", "Published"],
  ["analytics", "Analytics"], ["revenue", "Revenue"], ["experiments", "Experiments"],
  ["campaigns", "Campaigns"], ["costs", "Costs"], ["settings", "Settings"],
  ["case-lantern", "Case Lantern"],
  ["strategy-report", "Strategy Report"], ["watchlists", "Watchlists"],
  ["system-health", "System Health"]
] as const;

export const sectionKeys = navigation.map(([key]) => key);

export function Shell({ section, children, demo = true }: { section: string; children: React.ReactNode; demo?: boolean }) {
  const title = navigation.find(([key]) => key === section)?.[1] ?? "DealForge";
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">D</span><div><b>DealForge</b><small>PROFIT OS</small></div></div>
        <nav>{navigation.map(([key, label]) => <Link className={section === key ? "active" : ""} href={`/${key}`} key={key}><span>{navIcon(key)}</span>{label}</Link>)}</nav>
        <div className="sidebar-foot"><div className="pulse"/><div><b>{demo ? "Demo mode" : "Live mode"}</b><small>{demo ? "Zero credentials required" : "Safety gates active"}</small></div></div>
      </aside>
      <main>
        <header><div><p className="eyebrow">AFFILIATE OPERATIONS</p><h1>{title}</h1></div><div className="header-actions"><span className="status"><i/>Systems healthy</span><Link href="/settings" className="avatar">DF</Link></div></header>
        <div className="page">{children}</div>
      </main>
    </div>
  );
}

function navIcon(key: string) {
  const icons: Record<string, string> = { overview: "◫", products: "◇", deals: "↘", opportunities: "◆", seo: "⌕", "affiliate-programs": "%", content: "✦", "content-queue": "≡", published: "✓", analytics: "⌁", revenue: "$", experiments: "⌬", campaigns: "◎", costs: "−", "case-lantern": "◐", "strategy-report": "↗", watchlists: "◉", settings: "⚙", "system-health": "◉" };
  return icons[key] ?? "·";
}
