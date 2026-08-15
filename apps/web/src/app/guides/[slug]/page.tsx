import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { GuideCard, PublicLayout } from "@/components/PublicSite";
import { getGuide, guides, site } from "@/lib/site";

type Params = Promise<{ slug: string }>;

export function generateStaticParams() {
  return guides.map(({ slug }) => ({ slug }));
}

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const guide = getGuide((await params).slug);
  if (!guide) return {};
  return { title: guide.title, description: guide.description, alternates: { canonical: `/guides/${guide.slug}` }, openGraph: { title: guide.title, description: guide.description, type: "article", url: `${site.url}/guides/${guide.slug}` } };
}

export default async function GuidePage({ params }: { params: Params }) {
  const guide = getGuide((await params).slug);
  if (!guide) notFound();
  const related = guides.filter((item) => item.slug !== guide.slug).slice(0, 3);
  const schema = { "@context": "https://schema.org", "@type": "Article", headline: guide.title, description: guide.description, dateModified: "2026-08-15", author: { "@type": "Organization", name: site.name }, publisher: { "@type": "Organization", name: site.name }, mainEntityOfPage: `${site.url}/guides/${guide.slug}` };

  return (
    <PublicLayout>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema).replaceAll("<", "\\u003c") }} />
      <article className="article-wrap">
        <nav className="breadcrumbs" aria-label="Breadcrumb"><Link href="/">Home</Link><span>/</span><Link href="/guides">Guides</Link><span>/</span><b>{guide.category}</b></nav>
        <header className="article-hero">
          <div className="article-meta"><span>{guide.category}</span><span>{guide.intent}</span><span>{guide.readMinutes} minute read</span></div>
          <h1>{guide.title}</h1>
          <p>{guide.description}</p>
          <small>Updated {guide.updated} · Workspace Signal Editorial</small>
        </header>
        <div className="article-layout">
          <aside className="takeaway-card"><p>Signal summary</p><b>What matters most</b><ul>{guide.takeaways.map((takeaway) => <li key={takeaway}>{takeaway}</li>)}</ul></aside>
          <div className="article-body">
            <div className="article-disclosure"><b>Editorial note</b><p>This guide is educational and contains no paid placement. Future affiliate links will be clearly disclosed and will not change our evaluation criteria.</p></div>
            {guide.sections.map((section) => <section key={section.heading}><h2>{section.heading}</h2>{section.paragraphs.map((paragraph) => <p key={paragraph}>{paragraph}</p>)}{section.bullets && <ul>{section.bullets.map((bullet) => <li key={bullet}>{bullet}</li>)}</ul>}</section>)}
            <section><h2>Before you buy</h2><p>Confirm dimensions, compatibility, current price, shipping, return terms, and warranty directly with the merchant. Product specifications and availability can change after publication.</p></section>
          </div>
        </div>
      </article>
      <section className="public-section related-guides"><div className="public-section-head"><div><p className="public-kicker">Continue planning</p><h2>Related workspace guides</h2></div></div><div className="guide-grid compact">{related.map((item) => <GuideCard guide={item} key={item.slug} />)}</div></section>
    </PublicLayout>
  );
}
