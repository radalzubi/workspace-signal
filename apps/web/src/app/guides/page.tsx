import type { Metadata } from "next";
import { GuideCard, PublicLayout } from "@/components/PublicSite";
import { guides } from "@/lib/site";

export const metadata: Metadata = {
  title: "Workspace Guides",
  description: "Practical buying, setup, organization, ergonomic, and technology guides for better home workspaces.",
  alternates: { canonical: "/guides" },
};

export default function GuidesPage() {
  return (
    <PublicLayout>
      <section className="public-page-hero">
        <p className="public-kicker"><span /> Workspace library</p>
        <h1>Make every square inch work harder.</h1>
        <p>Start with a constraint, understand the tradeoffs, and buy only when the product genuinely improves the setup.</p>
      </section>
      <section className="public-section guide-archive">
        <div className="archive-filter" aria-label="Guide categories"><b>All guides</b><span>Small spaces</span><span>Ergonomics</span><span>Organization</span><span>Technology</span></div>
        <div className="guide-grid compact">{guides.map((guide) => <GuideCard guide={guide} key={guide.slug} />)}</div>
      </section>
    </PublicLayout>
  );
}
