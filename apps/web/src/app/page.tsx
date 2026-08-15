import type { Metadata } from "next";
import Link from "next/link";
import { EditorialNotice, GuideCard, PublicLayout } from "@/components/PublicSite";
import { guides, site } from "@/lib/site";

export const metadata: Metadata = {
  title: "Workspace Signal — Smarter upgrades for better workspaces",
  description: site.description,
  alternates: { canonical: "/" },
};

export default function Home() {
  return (
    <PublicLayout>
      <section className="public-hero">
        <div className="hero-copy">
          <p className="public-kicker"><span /> Independent workspace intelligence</p>
          <h1>Build a workspace that earns its space.</h1>
          <p className="hero-deck">Practical guides, careful comparisons, and verified deal context for home offices—built around usefulness, fit, and value.</p>
          <div className="hero-actions">
            <Link className="public-primary" href="/guides">Browse workspace guides <span>→</span></Link>
            <Link className="public-secondary" href="/methodology">How we evaluate</Link>
          </div>
          <dl className="hero-proof">
            <div><dt>01</dt><dd>Problem-first research</dd></div>
            <div><dt>02</dt><dd>Verified product facts</dd></div>
            <div><dt>03</dt><dd>Profit never outranks fit</dd></div>
          </dl>
        </div>
        <div className="hero-scene" aria-label="Abstract organized workspace illustration">
          <div className="scene-signal"><span>WORKSPACE SIGNAL</span><b>Clearer choices.<br />Better work.</b></div>
          <div className="scene-monitor"><span>FIT SCORE</span><b>92</b><i /></div>
          <div className="scene-desk"><i /><i /><i /></div>
          <div className="scene-note">Useful &gt; popular</div>
        </div>
      </section>

      <section className="public-section featured-guides">
        <div className="public-section-head">
          <div><p className="public-kicker">Start with the constraint</p><h2>Guides for real workspace problems</h2></div>
          <Link className="text-link" href="/guides">View all guides <span>→</span></Link>
        </div>
        <div className="guide-grid"><GuideCard guide={guides[0]} featured /><GuideCard guide={guides[1]} /><GuideCard guide={guides[2]} /></div>
      </section>

      <section className="signal-principles">
        <div><p className="public-kicker light">The Workspace Signal standard</p><h2>Recommendations should answer one question:</h2><strong>Will this meaningfully improve the way you work?</strong></div>
        <ol>
          <li><span>01</span><div><b>Fit before features</b><p>We begin with the space, equipment, task, and user constraint.</p></div></li>
          <li><span>02</span><div><b>Facts before adjectives</b><p>Specifications, price context, and compatibility must be grounded.</p></div></li>
          <li><span>03</span><div><b>Value before commission</b><p>Affiliate economics are measured, but never allowed to manufacture a recommendation.</p></div></li>
        </ol>
      </section>

      <section className="public-section latest-guides">
        <div className="public-section-head"><div><p className="public-kicker">Workspace library</p><h2>Plan the whole setup</h2></div></div>
        <div className="guide-grid compact">{guides.slice(3, 9).map((guide) => <GuideCard guide={guide} key={guide.slug} />)}</div>
      </section>

      <section className="public-section"><EditorialNotice /></section>

      <section className="public-cta">
        <p className="public-kicker light">Make the next upgrade count</p>
        <h2>Start with the problem—not the product.</h2>
        <Link className="public-primary pale" href="/guides">Find the right guide <span>→</span></Link>
      </section>
    </PublicLayout>
  );
}
