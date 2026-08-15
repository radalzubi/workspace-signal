import type { Metadata } from "next";
import Link from "next/link";
import { PublicLayout } from "@/components/PublicSite";
import { productPicks, site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Verified Workspace Product Shortlist",
  description: "A fact-checked shortlist of real workspace products, with current price observations, fit notes, and important compatibility limits.",
  alternates: { canonical: "/picks" },
};

function money(value: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

export default function PicksPage() {
  const schema = {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: "Workspace Signal verified product shortlist",
    url: `${site.url}/picks`,
    itemListElement: productPicks.map((product, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: product.name,
      url: `${site.url}/picks#${product.slug}`,
    })),
  };

  return (
    <PublicLayout>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema).replaceAll("<", "\\u003c") }} />
      <section className="public-page-hero picks-hero">
        <p className="public-kicker"><span /> Verified merchant research</p>
        <h1>Real products. Clear fit. No invented claims.</h1>
        <p>Our first shortlist focuses on desk charging and docking products with strong problem-solution fit and a transparent affiliate path.</p>
      </section>

      <section className="public-section picks-section">
        <div className="commercial-status">
          <div><span>Current link status</span><b>Normal merchant links</b></div>
          <p>Workspace Signal does not currently earn from these links. Anker publicly lists an 8% affiliate rate and 30-day cookie, but commissions begin only after program approval and replacement with authorized tracking links.</p>
          <Link href="/affiliate-disclosure">Read our disclosure →</Link>
        </div>

        <div className="pick-grid">
          {productPicks.map((product, index) => (
            <article className="pick-card" id={product.slug} key={product.slug}>
              <div className="pick-rank"><span>{String(index + 1).padStart(2, "0")}</span><b>{product.category}</b></div>
              <div className="pick-main">
                <p className="pick-brand">{product.brand} · Official US store</p>
                <h2>{product.name}</h2>
                <p className="pick-best"><b>Best for:</b> {product.bestFor}</p>
                <ul>{product.facts.map((fact) => <li key={fact}>{fact}</li>)}</ul>
                <div className="pick-warning"><b>Check before buying</b><p>{product.caution}</p></div>
              </div>
              <aside className="pick-economics">
                <span>Observed price</span>
                <strong>{money(product.price)}</strong>
                <small>Checked {product.observed}; verify at merchant.</small>
                <dl>
                  <div><dt>Public program rate</dt><dd>{product.publicProgramRate}%</dd></div>
                  <div><dt>Possible commission</dt><dd>{money(product.estimatedCommissionIfApproved)}</dd></div>
                  <div><dt>Commission today</dt><dd>$0.00</dd></div>
                </dl>
                <a className="public-primary" href={product.merchantUrl} target="_blank" rel="noopener noreferrer">Check at Anker <span>↗</span></a>
                <small className="normal-link-label">Normal merchant link · not yet an affiliate link</small>
              </aside>
            </article>
          ))}
        </div>
      </section>

      <section className="public-cta">
        <p className="public-kicker light">Choose by constraint</p>
        <h2>Not sure which product format fits?</h2>
        <Link className="public-primary pale" href="/guides/desk-charging-station-setup">Read the charging-station guide <span>→</span></Link>
      </section>
    </PublicLayout>
  );
}
