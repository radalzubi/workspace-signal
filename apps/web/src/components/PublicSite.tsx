import Link from "next/link";
import type { Guide } from "@/lib/site";
import { site } from "@/lib/site";

export function PublicHeader() {
  return (
    <header className="public-header">
      <Link className="public-brand" href="/" aria-label="Workspace Signal home">
        <span className="signal-mark" aria-hidden="true"><i /><i /><i /></span>
        <span><b>Workspace</b> Signal</span>
      </Link>
      <nav aria-label="Primary navigation">
        <Link href="/guides">Guides</Link>
        <Link href="/methodology">How we evaluate</Link>
        <Link href="/about">About</Link>
      </nav>
      <Link className="public-nav-cta" href="/guides">Explore guides <span>→</span></Link>
    </header>
  );
}

export function PublicFooter() {
  return (
    <footer className="public-footer">
      <div className="footer-lead">
        <div className="public-brand"><span className="signal-mark" aria-hidden="true"><i /><i /><i /></span><span><b>Workspace</b> Signal</span></div>
        <p>{site.tagline}</p>
      </div>
      <div>
        <b>Explore</b>
        <Link href="/guides">All guides</Link>
        <Link href="/methodology">Editorial methodology</Link>
        <Link href="/about">About</Link>
      </div>
      <div>
        <b>Information</b>
        <Link href="/affiliate-disclosure">Affiliate disclosure</Link>
        <Link href="/privacy">Privacy</Link>
        <Link href="/terms">Terms</Link>
        <Link href="/contact">Contact</Link>
      </div>
      <p className="footer-bottom">© {new Date().getFullYear()} Workspace Signal. Product facts and prices should be verified at the merchant before purchase.</p>
    </footer>
  );
}

export function PublicLayout({ children }: { children: React.ReactNode }) {
  return <div className="public-site"><PublicHeader /><main>{children}</main><PublicFooter /></div>;
}

export function GuideCard({ guide, featured = false }: { guide: Guide; featured?: boolean }) {
  return (
    <article className={`guide-card${featured ? " guide-card-featured" : ""}`}>
      <div className={`guide-visual guide-visual-${guide.category.toLowerCase().replaceAll(" ", "-")}`} aria-hidden="true">
        <span>{categoryGlyph(guide.category)}</span>
        <i /><i />
      </div>
      <div className="guide-card-body">
        <div className="guide-meta"><span>{guide.category}</span><span>{guide.readMinutes} min read</span></div>
        <h3><Link href={`/guides/${guide.slug}`}>{guide.title}</Link></h3>
        <p>{guide.description}</p>
        <Link className="text-link" href={`/guides/${guide.slug}`}>Read the guide <span>→</span></Link>
      </div>
    </article>
  );
}

function categoryGlyph(category: string) {
  const glyphs: Record<string, string> = {
    "Monitor Arms": "↗", "Cable Management": "⌁", "Budget Upgrades": "$",
    "Small Spaces": "⌂", "Desk Technology": "⌨", Organization: "▦",
    "Laptop Stands": "△", Lighting: "✦", Ergonomics: "◒", Charging: "ϟ",
  };
  return glyphs[category] ?? "◆";
}

export function EditorialNotice() {
  return (
    <aside className="editorial-notice">
      <span>Independent methodology</span>
      <p>We separate product fit from affiliate economics. A higher commission does not produce a higher editorial ranking.</p>
      <Link href="/methodology">See how evaluation works →</Link>
    </aside>
  );
}
